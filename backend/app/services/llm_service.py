import os
import json
import logging
import re
import time
import httpx
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
from threading import Lock
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from app.core.constants import SIGN_RULERS, SIGN_KEYWORDS

logger = logging.getLogger("nakshatra-backend")

# ----- Load env and validate -----
load_dotenv()
LLM_PROVIDER = (os.getenv("LLM_PROVIDER") or "groq").strip().lower()
if LLM_PROVIDER not in {"groq", "cerebras"}:
    logger.warning("Unsupported LLM_PROVIDER=%s, defaulting to groq", LLM_PROVIDER)
    LLM_PROVIDER = "groq"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_DEFAULT_MODEL = "llama3.1-8b"
CEREBRAS_DEFAULT_REPAIR_MODEL = "llama3.1-8b"


def extract_message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))
        return "\n".join(part for part in parts if part).strip()
    if content is None:
        return ""
    return str(content)


def format_llm_exception(exc: Exception) -> str:
    parts = [exc.__class__.__name__]
    status_code = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    if status_code is None and response is not None:
        status_code = getattr(response, "status_code", None)
    if status_code is not None:
        parts.append(f"status={status_code}")

    body = getattr(exc, "body", None)
    if body:
        try:
            parts.append(json.dumps(body))
        except TypeError:
            parts.append(str(body))
    else:
        text = str(exc).strip()
        if text:
            parts.append(text)
    return " | ".join(part for part in parts if part)


def is_quota_or_rate_limit_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    if status_code is None and response is not None:
        status_code = getattr(response, "status_code", None)
    if status_code == 429:
        return True

    body = getattr(exc, "body", None)
    candidate_text = [str(exc)]
    if body is not None:
        try:
            candidate_text.append(json.dumps(body))
        except TypeError:
            candidate_text.append(str(body))
    joined = " ".join(part for part in candidate_text if part).lower()
    markers = (
        "rate limit",
        "quota",
        "too many requests",
        "resource exhausted",
        "limit reached",
        "limit exceeded",
        "requests/day",
        "tokens/day",
        "daily limit",
        "rate-limited",
    )
    return any(marker in joined for marker in markers)


class LangChainProviderClient:
    def __init__(self, name: str, client: Optional[Any]):
        self.name = name
        self.client = client

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def invoke(self, prompt: str) -> Any:
        if not self.client:
            raise RuntimeError(f"{self.name} provider is not configured")
        return self.client.invoke(prompt)


class CerebrasFallbackClient:
    name = "cerebras"

    def __init__(self, api_key: Optional[str], model: str, max_tokens: int, timeout: int = 90):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.url = "https://api.cerebras.ai/v1/chat/completions"

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def invoke(self, prompt: str) -> AIMessage:
        if not self.api_key:
            raise RuntimeError("CEREBRAS_API_KEY environment variable is required for failover")

        last_error: Optional[Exception] = None
        for attempt in range(3):
            try:
                response = httpx.post(
                    self.url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "User-Agent": "Nakshatra-AI/1.0",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_completion_tokens": self.max_tokens,
                    },
                    timeout=self.timeout,
                )
            except httpx.HTTPError as exc:
                last_error = RuntimeError(f"Cerebras API request failed: {exc}")
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise last_error from exc

            if response.status_code == 429 and attempt < 2:
                retry_after = response.headers.get("retry-after")
                delay_seconds = 1.5 * (attempt + 1)
                if retry_after:
                    try:
                        delay_seconds = max(delay_seconds, float(retry_after))
                    except ValueError:
                        pass
                logger.warning(
                    "Cerebras returned 429 for model=%s; retrying in %.1fs (attempt %s/3)",
                    self.model,
                    delay_seconds,
                    attempt + 1,
                )
                time.sleep(delay_seconds)
                continue

            if response.is_error:
                detail_text = response.text.strip()
                try:
                    detail = response.json()
                except json.JSONDecodeError:
                    detail = detail_text
                raise RuntimeError(f"Cerebras API error ({response.status_code}): {detail}")

            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError("Cerebras API returned no choices")

            message = choices[0].get("message") or {}
            content = extract_message_text(message.get("content")).strip()
            if not content:
                raise RuntimeError("Cerebras API returned an empty message")
            return AIMessage(content=content)

        if last_error:
            raise last_error
        raise RuntimeError("Cerebras API request failed after retries")


def select_provider_order(
    preferred_provider: str,
    groq_provider: Optional[LangChainProviderClient],
    cerebras_provider: Optional[CerebrasFallbackClient],
) -> List[Any]:
    ordered = []
    if preferred_provider == "cerebras":
        ordered = [cerebras_provider, groq_provider]
    else:
        ordered = [groq_provider, cerebras_provider]
    return [provider for provider in ordered if provider and provider.enabled]


def invoke_with_failover(providers: List[Any], prompt: str, *, context: str) -> AIMessage:
    if not providers:
        raise RuntimeError("No LLM providers are configured")

    last_exc: Optional[Exception] = None
    for index, provider in enumerate(providers):
        try:
            response = provider.invoke(prompt)
            response_text = extract_message_text(getattr(response, "content", response)).strip()
            if response_text:
                level = logger.info if index == 0 else logger.warning
                label = "primary" if index == 0 else "fallback"
                level("LLM request for %s served by %s provider %s", context, label, provider.name)
                if isinstance(response, AIMessage):
                    return response
                return AIMessage(content=response_text)

            logger.warning("LLM provider %s returned empty content during %s", provider.name, context)
        except Exception as exc:
            last_exc = exc
            if is_quota_or_rate_limit_error(exc):
                logger.warning(
                    "LLM provider %s hit quota/rate limit during %s. Details: %s",
                    provider.name,
                    context,
                    format_llm_exception(exc),
                )
            else:
                logger.warning(
                    "LLM provider %s failed during %s. Details: %s",
                    provider.name,
                    context,
                    format_llm_exception(exc),
                )

    if last_exc:
        raise last_exc
    raise RuntimeError(f"All LLM providers returned empty content during {context}")


class SessionChatMemory:
    def __init__(self) -> None:
        self.messages: List[Any] = []

    def add_message(self, message: Any) -> None:
        self.messages.append(message)

    def add_user_message(self, content: str) -> None:
        self.messages.append(HumanMessage(content=content))

    def add_ai_message(self, content: str) -> None:
        self.messages.append(AIMessage(content=content))


class SessionConversationState:
    def __init__(self) -> None:
        self.memory = type("MemoryContainer", (), {"chat_memory": SessionChatMemory()})()


GROQ_DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20B").strip()
GROQ_DEFAULT_REPAIR_MODEL = os.getenv("GROQ_REPAIR_MODEL", "openai/gpt-oss-20B").strip()

# ----- Shared LLM client -----
groq_llm = LangChainProviderClient(
    "groq",
    ChatGroq(
        model=GROQ_DEFAULT_MODEL,
        api_key=GROQ_API_KEY,
        max_tokens=1400,
        timeout=90,
        max_retries=3,
    ) if GROQ_API_KEY else None,
)

groq_repair_llm = LangChainProviderClient(
    "groq",
    ChatGroq(
        model=GROQ_DEFAULT_REPAIR_MODEL,
        api_key=GROQ_API_KEY,
        max_tokens=220,
        timeout=90,
        max_retries=2,
    ) if GROQ_API_KEY else None,
)

cerebras_llm = CerebrasFallbackClient(
    api_key=CEREBRAS_API_KEY,
    model=os.getenv("CEREBRAS_MODEL", CEREBRAS_DEFAULT_MODEL),
    max_tokens=1400,
    timeout=90,
)

cerebras_repair_llm = CerebrasFallbackClient(
    api_key=CEREBRAS_API_KEY,
    model=os.getenv("CEREBRAS_REPAIR_MODEL", os.getenv("CEREBRAS_MODEL", CEREBRAS_DEFAULT_REPAIR_MODEL)),
    max_tokens=220,
    timeout=90,
)

llm_providers = select_provider_order(LLM_PROVIDER, groq_llm, cerebras_llm)
repair_llm_providers = select_provider_order(LLM_PROVIDER, groq_repair_llm, cerebras_repair_llm)

if not llm_providers or not repair_llm_providers:
    logger.error("No usable LLM provider is configured")
    raise RuntimeError("At least one LLM provider must be configured")

logger.info("LLM provider order: %s", " -> ".join(provider.name for provider in llm_providers))
logger.info("Repair LLM provider order: %s", " -> ".join(provider.name for provider in repair_llm_providers))
if not groq_llm.enabled:
    logger.info("Groq primary disabled; GROQ_API_KEY not configured")
if cerebras_llm.enabled:
    logger.info(
        "Cerebras provider enabled with chat model=%s repair model=%s",
        cerebras_llm.model,
        cerebras_repair_llm.model,
    )
else:
    logger.info("Cerebras provider disabled; CEREBRAS_API_KEY not configured")


# ----- Per-session stores (thread-safe) -----
_chain_store: Dict[str, SessionConversationState] = {}
_chain_lock = Lock()


def create_chain_for_session(session_id: str) -> SessionConversationState:
    chain = SessionConversationState()
    logger.info("create_chain_for_session: created chain id=%s for session_id=%s", id(chain), session_id)
    return chain


def get_or_create_chain(session_id: str) -> SessionConversationState:
    with _chain_lock:
        logger.info("LOOKUP: session_id=%r keys=%s pid=%s", session_id, list(_chain_store.keys()), os.getpid())
        chain = _chain_store.get(session_id)
        if chain is None:
            chain = create_chain_for_session(session_id)
            _chain_store[session_id] = chain
            logger.info("STORE: stored chain for session_id=%r (keys now=%s) pid=%s", session_id, list(_chain_store.keys()), os.getpid())
        else:
            logger.info("REUSE: reusing chain id=%s for session_id=%r pid=%s", id(chain), session_id, os.getpid())
        return chain


def get_first_name(full_name: Optional[str]) -> str:
    if not full_name:
        return "there"
    cleaned = str(full_name).strip()
    if not cleaned:
        return "there"
    return cleaned.split()[0]


def classify_response_mode(user_query: Optional[str], is_first_message: bool = False) -> str:
    if is_first_message:
        return "quick_scan"

    query = (user_query or "").lower()
    deep_dive_markers = [
        "explain everything",
        "in detail",
        "in details",
        "detailed",
        "detail please",
        "deep dive",
        "elaborate",
        "thorough",
        "comprehensive",
        "full analysis",
        "complete analysis",
        "step by step",
    ]
    if any(marker in query for marker in deep_dive_markers):
        return "deep_dive"
    return "normal_qa"


def build_response_style_instructions(user_query: Optional[str] = None, is_first_message: bool = False) -> str:
    mode = classify_response_mode(user_query, is_first_message=is_first_message)
    if mode == "quick_scan":
        return (
            "### Response Mode: Quick Scan\n"
            "- Length target: 150 to 200 words.\n"
            "- Use short structured sections.\n"
            "- Make it welcoming, insightful, and easy to scan.\n"
            "- Focus on 3 to 4 strong chart signatures, then end with a warm next-step prompt.\n"
            "- Do not turn this into a long technical analysis.\n"
        )
    if mode == "deep_dive":
        return (
            "### Response Mode: Deep Dive\n"
            "- Length target: 500 to 800 words.\n"
            "- Use clear Markdown headers and sub-sections.\n"
            "- Explain the astrological factors in depth and translate them into lived experience.\n"
            "- Include strengths, challenges, timing if relevant, and practical guidance.\n"
            "- End with a short remedies or suggestions section when relevant.\n"
            "- Do not cut the answer off abruptly or compress it into tiny bullets.\n"
        )
    return (
        "### Response Mode: Normal Q&A\n"
        "- Length target: 200 to 400 words.\n"
        "- Use 2 to 4 short sections with bold headers when helpful.\n"
        "- Answer the user's actual question directly, then support it with chart evidence.\n"
        "- Keep the answer substantial but not overwhelming.\n"
        "- Avoid one-line bullet dumps or unfinished sentences.\n"
    )


def infer_question_focus(user_query: Optional[str]) -> Dict[str, Any]:
    query = (user_query or "").lower()
    topic = "general"
    relevant_houses = [1]
    relevant_karakas = ["Lagna lord", "Moon", "Sun"]
    supporting_charts: list[str] = []
    remedies_relevant = False
    timing_focus = any(token in query for token in ["when", "timing", "time", "period", "dasha"])
    topic_guidance = (
        "Anchor the answer in Lagna, Lagna lord, Moon, and the most defining chart signatures. "
        "If the question is broad or unclear, give a balanced general reading before narrowing down."
    )

    if any(token in query for token in ["marriage", "spouse", "wife", "husband", "partner", "relationship", "love", "romance"]):
        topic = "marriage_relationships"
        relevant_houses = [1, 5, 7, 8, 12]
        relevant_karakas = ["Venus", "Jupiter", "Moon", "7th lord"]
        supporting_charts = ["D9"]
        remedies_relevant = True
        timing_focus = True
        topic_guidance = (
            "Focus first on the 7th house, its lord, Venus, and relationship-supporting influences from the 5th and 8th houses. "
            "Use D9 as supporting evidence for spouse quality, marriage stability, and deeper relational dharma. "
            "For timing, prioritize dashas and antardashas activating the 7th lord, Venus, planets placed in the 7th house, or strong links to the 7th/D9."
        )
    elif any(token in query for token in ["career", "profession", "job", "work", "business", "promotion", "status"]):
        topic = "career"
        relevant_houses = [1, 2, 6, 10, 11]
        relevant_karakas = ["Sun", "Saturn", "Mercury", "10th lord"]
        supporting_charts = ["D10"]
        remedies_relevant = True
        timing_focus = True
        topic_guidance = (
            "Prioritize the 10th house, 10th lord, 6th house, 2nd house, and 11th house for role, effort, earnings, and gains. "
            "Use Sun, Saturn, Mercury, and D10 as supporting evidence for profession, status, and public work. "
            "For timing, emphasize periods activating the 10th lord, planets influencing the 10th, or key D10 connections."
        )
    elif any(token in query for token in ["child", "children", "kid", "kids", "offspring", "pregnancy", "fertility", "son", "daughter"]):
        topic = "children"
        relevant_houses = [2, 5, 9, 11]
        relevant_karakas = ["Jupiter", "Moon", "5th lord"]
        remedies_relevant = True
        topic_guidance = (
            "Focus on the 5th house, 5th lord, Jupiter, relevant occupants, and helpful or difficult aspects. "
            "Distinguish promise, delay, and support factors carefully instead of giving a blanket yes or no."
        )
    elif any(token in query for token in ["sibling", "siblings", "brother", "brothers", "sister", "sisters"]):
        topic = "siblings"
        relevant_houses = [3, 11]
        relevant_karakas = ["Mercury", "Mars", "3rd lord", "11th lord"]
        topic_guidance = (
            "Use the 3rd house and its lord for younger siblings, and the 11th house and its lord for elder siblings. "
            "Use Mercury and Mars as supporting karakas and explain whether the indications are harmonious, distant, or mixed."
        )
    elif any(token in query for token in ["friend", "friends", "friendship", "social circle", "network", "companions"]):
        topic = "friends_social_circle"
        relevant_houses = [3, 11]
        relevant_karakas = ["Mercury", "Moon", "Venus", "11th lord", "3rd lord"]
        topic_guidance = (
            "Focus on the 3rd and 11th houses for companions, peers, networks, and the type of social support the native attracts. "
            "Use Mercury, Moon, and Venus as supporting indicators of communication style, emotional rapport, and social ease. "
            "Explain what kind of friends are likely, how stable the circles are, and whether the native draws practical, intellectual, spiritual, or mixed company."
        )
    elif any(token in query for token in ["money", "wealth", "finance", "income", "rich", "prosperity"]):
        topic = "wealth"
        relevant_houses = [2, 5, 9, 11]
        relevant_karakas = ["Jupiter", "Venus", "2nd lord", "11th lord"]
        remedies_relevant = True
        topic_guidance = (
            "Focus on the 2nd and 11th houses for wealth and gains, and the 5th and 9th for fortune, merit, and supportive prosperity patterns. "
            "Check dhana yogas, the condition of Jupiter and Venus, and whether wealth comes more through skill, business, support networks, or luck."
        )
    elif any(token in query for token in ["health", "disease", "illness", "body", "hospital"]):
        topic = "health"
        relevant_houses = [1, 6, 8, 12]
        relevant_karakas = ["Sun", "Moon", "Mars", "Saturn", "6th lord"]
        remedies_relevant = True
        topic_guidance = (
            "Focus on the 1st house for vitality, the 6th for disease and imbalance, the 8th for chronic vulnerability, and the 12th for hospitalization or depletion. "
            "Describe tendencies and stress points carefully without pretending to offer medical diagnosis."
        )
    elif any(token in query for token in ["spiritual", "spirituality", "purpose", "dharma", "moksha", "meditation", "soul", "guru", "inner growth", "enlightenment"]):
        topic = "spirituality"
        relevant_houses = [1, 5, 9, 12]
        relevant_karakas = ["Jupiter", "Ketu", "Sun", "Moon", "9th lord", "12th lord"]
        supporting_charts = ["D9"]
        topic_guidance = (
            "Focus on the 5th, 9th, and 12th houses for mantra shakti, dharma, grace, retreat, and liberation-oriented tendencies. "
            "Use Jupiter, Ketu, Sun, Moon, and D9 as supporting indicators of faith, inner calling, and spiritual maturation."
        )
    elif any(token in query for token in ["sensual", "sexual", "intimacy", "passion"]):
        topic = "sensuality_intimacy"
        relevant_houses = [1, 5, 7, 8, 12]
        relevant_karakas = ["Venus", "Mars", "Moon"]
        supporting_charts = ["D9"]
        topic_guidance = (
            "Focus on Venus, Mars, Moon, and the 5th, 7th, 8th, and 12th houses to judge attraction, chemistry, passion, emotional bonding, and private intimacy patterns."
        )
    elif any(token in query for token in ["death", "longevity", "end of life"]):
        topic = "longevity_sensitive"
        relevant_houses = [1, 3, 8]
        relevant_karakas = ["Saturn", "8th lord"]
        topic_guidance = (
            "Handle longevity cautiously. Focus on vitality, resilience, and difficult periods rather than deterministic death claims. "
            "Use the 1st, 3rd, and 8th houses, Saturn, and the 8th lord for risk and downtime patterns."
        )
    elif timing_focus:
        topic = "timing_general"
        relevant_houses = [1, 9, 10]
        relevant_karakas = ["Mahadasha lord", "Antardasha lord", "Moon"]
        topic_guidance = (
            "The user is primarily asking about timing. Start from the relevant life area if one is implied, then use the current and upcoming mahadasha and antardasha periods. "
            "Explain timing through activation of house lords, occupants, and key karakas rather than giving unsupported dates."
        )

    return {
        "topic": topic,
        "relevant_houses": relevant_houses,
        "relevant_karakas": relevant_karakas,
        "supporting_charts": supporting_charts,
        "timing_focus": timing_focus,
        "remedies_relevant": remedies_relevant,
        "topic_guidance": topic_guidance,
    }


def build_astrology_reasoning_framework(user_query: Optional[str] = None, is_first_message: bool = False) -> str:
    if is_first_message:
        return (
            "### Jyotish Reading Method\n"
            "1. Start from Lagna, Lagna lord, and Janma Nakshatra to establish the chart's core pattern.\n"
            "2. Highlight only the most important placements, yogas, and strengths that define the person.\n"
            "3. Translate technical combinations into lived personality, emotional pattern, promise, and life direction.\n"
            "4. Use the current dasha as the present life chapter.\n"
            "5. Keep the reading elegant, welcoming, and selective rather than exhaustive.\n"
        )

    focus = infer_question_focus(user_query)
    return (
        "### Astrological Reasoning Framework\n"
        "You are a seasoned Vedic astrologer (Jyotishi) reasoning step by step from the chart.\n"
        "1. Begin with Lagna and the Lagna lord to establish the person's baseline nature and life pattern.\n"
        f"2. For this question, prioritize houses {focus['relevant_houses']} and the key significators {focus['relevant_karakas']}.\n"
        "3. Judge each relevant house through: the house itself, its lord, planets occupying it, aspects, dignity, combustion, functional nature, and yogas.\n"
        "4. If divisional chart data is provided for this topic, use it as supporting evidence, never as a replacement for the natal chart.\n"
        "5. Use Vimshottari dasha for timing. When timing is supported, give clear windows from the provided dates. Do not invent dates.\n"
        "6. Every conclusion should be tied back to concrete chart evidence.\n"
        "7. If the chart is mixed, say the result is mixed and explain why instead of forcing certainty.\n"
        "8. When the topic naturally calls for help or correction, end with practical Vedic remedies.\n"
        f"9. Topic-specific guidance: {focus['topic_guidance']}\n"
        f"10. Topic metadata: {json.dumps(focus, ensure_ascii=False)}\n"
    )


def build_inline_chart_prompt(
    chain: SessionConversationState,
    chart_summary: Optional[str],
    final_input: str,
) -> str:
    prompt_parts = []
    if chart_summary:
        prompt_parts.append(chart_summary)

    history_lines = []
    for message in chain.memory.chat_memory.messages:
        if isinstance(message, SystemMessage):
            continue
        if isinstance(message, HumanMessage) and message.content.strip() == "My birth details":
            continue
        if isinstance(message, HumanMessage):
            history_lines.append(f"User: {message.content}")
        elif isinstance(message, AIMessage):
            history_lines.append(f"Assistant: {message.content}")

    if history_lines:
        prompt_parts.append("RECENT CONVERSATION\n" + "\n".join(history_lines[-4:]))

    prompt_parts.append(final_input)
    return "\n\n".join(part for part in prompt_parts if part)


def build_kundli_prompt(
    kundli: Dict[str, Any],
    profile: Optional[Dict[str, Any]],
    today: datetime,
    plan_access: Optional[Dict[str, Any]] = None,
) -> str:
    from app.services.astrology_service import build_detailed_chart_summary, build_free_tier_chart_summary
    
    plan_access = plan_access or {}
    is_premium = bool(plan_access.get("is_premium"))
    response_style = build_response_style_instructions(is_first_message=True)
    reasoning_framework = build_astrology_reasoning_framework(is_first_message=True)
    chart_summary = (
        build_detailed_chart_summary(kundli, profile)
        if is_premium
        else build_free_tier_chart_summary(kundli, profile)
    )
    first_name = get_first_name((profile or {}).get("full_name"))
    
    if is_premium:
        core_rules = (
            "You are writing the very first message inside Nakshatra AI after a user submits birth details.\n"
            "You are a master Vedic astrologer (Jyotishi) with decades of practice. Use only the provided chart data. Do not use western terminology.\n\n"
            "### Core Rules\n"
            "1. NEVER ask for birth details. They are already available.\n"
            "2. DO NOT recalculate Mahadasha or Antardasha. Use the given data only.\n"
            "3. This message should feel premium, insightful, human, and welcoming, not like a raw placement dump.\n"
            "4. Focus on what is special about the chart: baseline nature, hidden emotional layer, promise/potential, and the current dasha-gochar chapter.\n"
            "5. Mention only 3 to 4 chart signatures that are genuinely the most compelling.\n"
            "6. If a yoga is strong, present it confidently in plain language. If a yoga is conditional, mention it only with nuance.\n"
            "7. Use crisp, premium Markdown formatting with bold headers and tasteful emojis. No tables.\n"
            f"8. End with one warm, concise prompt inviting the user to choose one of: career, relationships, or deeper purpose.\n"
            "9. Follow the response mode instructions exactly for length and depth.\n\n"
            "### Output Format (must follow this structure)\n"
            f"## 🌌 Welcome to your Nakshatra AI reading, {first_name}\n"
            "A short 2-sentence opening that captures the user's chart essence.\n"
            "### ✨ **What stands out in your chart**\n"
            "One short paragraph.\n"
            "### 🌙 **Your hidden strength**\n"
            "One short paragraph.\n"
            "### 💠 **The promise in this chart**\n"
            "One short paragraph.\n"
            "### 🔮 **Your current chapter**\n"
            "One short paragraph using the current dasha together with the current gochar.\n"
            "Final line: a single warm question offering career, relationships, or purpose, with 1 to 3 tasteful emojis.\n\n"
            "### Style Guidance\n"
            "- Sound insightful, specific, and elegant.\n"
            "- Translate astrological combinations into lived experience.\n"
            "- Avoid sounding mechanical, generic, or overly mystical.\n"
            "- Do not overstate weak combinations as certainties.\n\n"
            "- Use bold emphasis for 1 to 2 key phrases in each section.\n"
            "- Make the message feel visually rich and easy to scan.\n"
            "- Emojis should feel refined, not loud or gimmicky.\n\n"
        )
    else:
        core_rules = (
            "You are writing the first free-tier reading inside Nakshatra AI after a user submits birth details.\n"
            "Use only the provided chart data and keep the experience warm, clear, and concise.\n\n"
            "### Free Tier Rules\n"
            "1. NEVER ask for birth details.\n"
            "2. Use the natal chart together with the current dasha and current gochar context. Do not rely on divisional charts, remedies, or premium extras.\n"
            "3. Keep this reading to 130 to 170 words.\n"
            "4. Focus on overall personality, one major strength, one growth theme, and the current chapter.\n"
            "5. End with a gentle note that deeper chart analysis is available in Premium.\n\n"
            "### Output Format\n"
            f"## 🌌 Welcome to your Nakshatra AI reading, {first_name}\n"
            "A short opening.\n"
            "### ✨ What stands out\n"
            "One short paragraph.\n"
            "### 🔮 Current chapter\n"
            "One short paragraph.\n"
            "Final line: one concise next-step note.\n\n"
        )

    prompt = f"""{core_rules}
{reasoning_framework}
{response_style}

### User Profile
{json.dumps({"full_name": (profile or {}).get("full_name"), "first_name": first_name}, indent=2)}

### Chart Context
{chart_summary}

### Today's Context
Date: {today.strftime('%Y-%m-%d')}
"""
    return prompt


def response_looks_incomplete(text: str) -> bool:
    stripped = (text or "").rstrip()
    if not stripped:
        return False
    if stripped.endswith(("...", "…", "—", "-", ":", ";")):
        return True
    if len(stripped.split()) < 25:
        return False
    return stripped[-1].isalnum()


def merge_continuation_text(response_text: str, continuation_text: str) -> str:
    base = (response_text or "").rstrip()
    addition = (continuation_text or "").lstrip()
    if not base or not addition:
        return base or addition

    max_overlap = min(len(base), len(addition), 40)
    overlap = 0
    for size in range(max_overlap, 0, -1):
        if base[-size:] == addition[:size]:
            overlap = size
            break

    if overlap:
        return f"{base}{addition[overlap:]}"

    if base[-1].isalnum() and addition[0].isalnum():
        return f"{base}{addition}"

    return f"{base} {addition}"


def complete_if_truncated(response_text: str) -> str:
    completed = response_text
    for _ in range(2):
        if not response_looks_incomplete(completed):
            return completed

        try:
            continuation = invoke_with_failover(
                repair_llm_providers,
                (
                    "Continue the following astrology answer naturally from exactly where it stopped.\n"
                    "Do not restart, do not repeat earlier points, and do not add meta commentary.\n"
                    "If the text was cut in the middle of a word, start with only the missing remainder of that word.\n"
                    "Finish the incomplete sentence and, if needed, add one brief concluding sentence only.\n\n"
                    f"Partial answer:\n{completed}"
                ),
                context="truncated response completion",
            )
            continuation_text = getattr(continuation, "content", str(continuation)).strip()
            if not continuation_text:
                return completed
            completed = merge_continuation_text(completed, continuation_text)
        except Exception:
            logger.exception("Failed to complete truncated response")
            return completed
    return completed


def prune_memory_keep_last(chain: SessionConversationState, keep_last_pairs: int = 1):
    msgs = chain.memory.chat_memory.messages
    if msgs:
        system_msgs = [msg for msg in msgs if isinstance(msg, SystemMessage)]
        conversation_msgs = [msg for msg in msgs if not isinstance(msg, SystemMessage)]
        chain.memory.chat_memory.messages = system_msgs + conversation_msgs[-(keep_last_pairs*2):]


def ensure_chart_summary_in_memory(chain: SessionConversationState, chart_summary: str) -> None:
    if not chart_summary:
        return
    for message in chain.memory.chat_memory.messages:
        if isinstance(message, SystemMessage) and message.content.strip() == chart_summary.strip():
            return
    chain.memory.chat_memory.add_message(SystemMessage(content=chart_summary))


def build_chat_retry_fallback_response(user_query: str, kundli_available: bool) -> str:
    if kundli_available:
        return (
            "I hit a temporary issue while generating the full reply, but I still have your chart context. "
            "Please send the same question once more and I’ll continue with a chart-based answer."
        )
    return (
        "I hit a temporary issue while generating the reply. Please send the question once more and I’ll continue."
    )


def build_no_credit_backend_failure_message(is_premium: bool) -> str:
    if is_premium:
        return (
            "We hit a temporary backend issue while preparing your reading. "
            "We know this was on our side. Please come back after some time."
        )
    return (
        "We hit a temporary backend issue while preparing your reading, and we know this was our fault. "
        "Your free credit was not used. Please come back after some time."
    )
