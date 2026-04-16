import os
import json
import logging
import re
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from threading import Lock
from contextlib import asynccontextmanager
from tempfile import TemporaryDirectory

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jyotichart import (
    JUPITER,
    KETU,
    MARS,
    MERCURY,
    MOON,
    NorthChart,
    RAHU,
    SATURN,
    SUN,
    SouthChart,
    VENUS,
)

from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import AIMessage, HumanMessage, SystemMessage

# from api.astrology import get_kundli_data // Can use freeastrologyapi.com to get kundli data
from astro.astro import (
    DEBILITATION_SIGNS,
    EXALTATION_SIGNS,
    MOOLATRIKONA_RANGES,
    OWN_SIGNS,
    generate_chart,
)
from database import connect_to_mongo, close_mongo_connection, get_sessions_collection
from models import SessionData, Message

# ----- Logging -----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nakshatra-backend")

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_RULERS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

SIGN_KEYWORDS = {
    "Aries": "direct, bold, action-oriented",
    "Taurus": "steady, sensual, security-seeking",
    "Gemini": "curious, adaptable, communicative",
    "Cancer": "protective, feeling-led, nurturing",
    "Leo": "expressive, proud, creative",
    "Virgo": "analytical, skillful, improvement-oriented",
    "Libra": "relational, aesthetic, balance-seeking",
    "Scorpio": "intense, strategic, private",
    "Sagittarius": "philosophical, optimistic, freedom-seeking",
    "Capricorn": "disciplined, pragmatic, status-aware",
    "Aquarius": "independent, unconventional, future-minded",
    "Pisces": "imaginative, compassionate, porous",
}

HOUSE_THEMES = {
    1: "self, vitality, appearance, and overall life direction",
    2: "speech, family, stored wealth, and values",
    3: "courage, communication, skills, and siblings",
    4: "home, mother, emotional foundations, and comforts",
    5: "intelligence, creativity, children, and merit",
    6: "work, conflict, debt, disease, and discipline",
    7: "partnership, marriage, agreements, and public dealings",
    8: "transformation, secrecy, vulnerability, and inheritance",
    9: "dharma, fortune, teachers, father, and higher guidance",
    10: "career, karma, reputation, and visible achievement",
    11: "gains, networks, ambitions, and elder siblings",
    12: "loss, retreat, sleep, foreign ties, and inner withdrawal",
}

PLANET_THEMES = {
    "Sun": "identity, vitality, authority",
    "Moon": "mind, emotions, nourishment",
    "Mars": "drive, assertion, conflict",
    "Mercury": "intellect, language, adaptability",
    "Jupiter": "wisdom, growth, guidance",
    "Venus": "love, pleasure, aesthetics",
    "Saturn": "duty, endurance, delay",
    "Rahu": "amplification, appetite, worldly desire",
    "Ketu": "detachment, insight, past-life residue",
}

PLANET_DISPLAY_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
PLANET_SORT_ORDER = {name: index for index, name in enumerate(PLANET_DISPLAY_ORDER)}

CHART_OPTIONS = {
    "D1": {"label": "Lagna / Rasi", "source": "natal"},
    "D9": {"label": "Navamsha", "source": "divisional"},
    "D10": {"label": "Dashamsha", "source": "divisional"},
}

CHART_STYLES = {"north", "south"}

JYOTI_PLANETS = {
    "Sun": SUN,
    "Moon": MOON,
    "Mars": MARS,
    "Mercury": MERCURY,
    "Jupiter": JUPITER,
    "Venus": VENUS,
    "Saturn": SATURN,
    "Rahu": RAHU,
    "Ketu": KETU,
}

PLANET_SHORT_SYMBOLS = {
    "Sun": "Su",
    "Moon": "Mo",
    "Mars": "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus": "Ve",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke",
}

# ----- Database Lifespan -----
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

# ----- App -----
app = FastAPI(title="Nakshatra AI Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nakshatra-ai.vercel.app",  # deployed frontend
       "http://localhost:3000",            # for local dev convenience
    ],
    allow_credentials=True,                 
    allow_methods=["*"],                    
    allow_headers=["*"],                    
)

@app.get("/ping")
def ping():
    """Used by frontend to cold-start backend."""
    logger.info("Ping received")
    return {"status": "ok"}

# ----- Load env and validate -----
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY is not set")
    raise RuntimeError("GROQ_API_KEY environment variable is required")

# ----- Shared LLM client -----
llm = ChatGroq(
    model="openai/gpt-oss-20B",
    api_key=GROQ_API_KEY,
    max_tokens=1400,
    timeout=90,
    max_retries=3,
)

repair_llm = ChatGroq(
    model="openai/gpt-oss-20B",
    api_key=GROQ_API_KEY,
    max_tokens=220,
    timeout=90,
    max_retries=2,
)

# ----- Per-session stores (thread-safe) -----
_kundli_store: Dict[str, Dict[str, Any]] = {}
_kundli_lock = Lock()

_chain_store: Dict[str, ConversationChain] = {}
_chain_lock = Lock()

_chart_summary_store: Dict[str, str] = {}
_chart_summary_lock = Lock()


def store_kundli(session_id: str, kundli: Dict[str, Any]) -> None:
    with _kundli_lock:
        _kundli_store[session_id] = kundli


def get_kundli(session_id: str) -> Optional[Dict[str, Any]]:
    with _kundli_lock:
        return _kundli_store.get(session_id)


def store_chart_summary(session_id: str, summary: str) -> None:
    with _chart_summary_lock:
        _chart_summary_store[session_id] = summary


def get_chart_summary(session_id: str) -> Optional[str]:
    with _chart_summary_lock:
        return _chart_summary_store.get(session_id)


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
            "Use the 1st, 3rd, and 8th houses, Saturn, and the 8th lord for risk and endurance patterns."
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
            continuation = repair_llm.invoke(
                (
                    "Continue the following astrology answer naturally from exactly where it stopped.\n"
                    "Do not restart, do not repeat earlier points, and do not add meta commentary.\n"
                    "If the text was cut in the middle of a word, start with only the missing remainder of that word.\n"
                    "Finish the incomplete sentence and, if needed, add one brief concluding sentence only.\n\n"
                    f"Partial answer:\n{completed}"
                )
            )
            continuation_text = getattr(continuation, "content", str(continuation)).strip()
            if not continuation_text:
                return completed
            completed = merge_continuation_text(completed, continuation_text)
        except Exception:
            logger.exception("Failed to complete truncated response")
            return completed
    return completed


def find_next_mahadasha(kundli: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    timeline = kundli.get("vimshottari_dasha", {}).get("mahadashas", [])
    for idx, maha in enumerate(timeline):
        if maha.get("is_current"):
            if idx + 1 < len(timeline):
                return timeline[idx + 1]
            return None
    return None


def summarize_planets(kundli: Dict[str, Any], names: list[str]) -> list[Dict[str, Any]]:
    planets = []
    for planet in kundli.get("planets", []):
        if planet.get("name") in names and "error" not in planet:
            nakshatra = planet.get("nakshatra", {})
            planets.append({
                "name": planet["name"],
                "sign": planet["sign"],
                "house": planet["house"],
                "retrograde": planet["retrograde"],
                "nakshatra": {
                    "name": nakshatra.get("name"),
                    "lord": nakshatra.get("lord"),
                    "pada": nakshatra.get("pada"),
                },
            })
    return planets


def summarize_vedic_aspects(kundli: Dict[str, Any], names: list[str]) -> Dict[str, Any]:
    vedic_aspects = kundli.get("vedic_aspects", {})
    by_planet = vedic_aspects.get("by_planet", {})
    summary = []

    for name in names:
        data = by_planet.get(name)
        if not data:
            continue
        summary.append({
            "planet": name,
            "house": data.get("house"),
            "sign": data.get("sign"),
            "aspects": [
                {
                    "aspect_name": aspect.get("aspect_name"),
                    "aspect_type": aspect.get("aspect_type"),
                    "target_house": aspect.get("target_house"),
                    "target_sign": aspect.get("target_sign"),
                    "target_planets": aspect.get("target_planets", []),
                }
                for aspect in data.get("aspects", [])
            ],
        })

    return {
        "node_basis": vedic_aspects.get("node_basis"),
        "by_planet": summary,
    }


def summarize_planetary_conditions(
    kundli: Dict[str, Any],
    names: list[str],
    user_query: Optional[str] = None,
) -> Dict[str, Any]:
    planetary_conditions = kundli.get("planetary_conditions", {})
    query = (user_query or "").lower()
    wants_combustion = any(token in query for token in ["combust", "combustion", "sun"])
    wants_functional = any(token in query for token in ["benefic", "malefic", "functional"])
    wants_dignity = any(
        token in query
        for token in ["exalt", "debil", "own sign", "moolatrikona", "strong", "weak", "strength"]
    )
    if not any([wants_combustion, wants_functional, wants_dignity]):
        wants_combustion = wants_functional = wants_dignity = True

    summary = {}
    for name in names:
        conditions = planetary_conditions.get(name)
        if not conditions:
            continue
        compact = {}
        dignity = conditions.get("dignity") or {}
        combustion = conditions.get("combustion") or {}
        functional = conditions.get("functional_nature") or {}

        if wants_dignity and dignity.get("status") not in {None, "not_applicable", "ordinary"}:
            compact["dignity"] = dignity.get("status")
        if wants_combustion and combustion.get("status") == "combust":
            compact["combustion"] = {
                "status": "combust",
                "distance_from_sun_deg": combustion.get("distance_from_sun_deg"),
            }
        if wants_functional and functional.get("status") not in {None, "not_applicable"}:
            compact["functional_nature"] = {
                "status": functional.get("status"),
                "ruled_houses": functional.get("ruled_houses", []),
            }

        if compact:
            summary[name] = compact
    return summary


def summarize_children_context(kundli: Dict[str, Any]) -> Dict[str, Any]:
    house_lords = (kundli.get("yoga_analysis", {}) or {}).get("house_lords", {})
    fifth_house = house_lords.get("5", {})
    fifth_lord_name = fifth_house.get("lord")

    planets = {
        planet.get("name"): planet
        for planet in kundli.get("planets", [])
        if "error" not in planet
    }
    fifth_lord = planets.get(fifth_lord_name) if fifth_lord_name else None
    jupiter = planets.get("Jupiter")
    occupants = sorted(
        [
            planet.get("name")
            for planet in kundli.get("planets", [])
            if "error" not in planet and planet.get("house") == 5
        ]
    )

    vedic_aspects = kundli.get("vedic_aspects", {})
    house_aspects = [
        {
            "from": aspect.get("from"),
            "aspect_name": aspect.get("aspect_name"),
            "aspect_type": aspect.get("aspect_type"),
        }
        for aspect in vedic_aspects.get("house_aspects", [])
        if aspect.get("to_house") == 5
    ]
    fifth_lord_aspects = [
        {
            "from": aspect.get("from"),
            "aspect_name": aspect.get("aspect_name"),
            "aspect_type": aspect.get("aspect_type"),
        }
        for aspect in vedic_aspects.get("planet_to_planet", [])
        if aspect.get("to") == fifth_lord_name
    ]

    conditions = kundli.get("planetary_conditions", {})

    return {
        "fifth_house": {
            "sign": fifth_house.get("sign"),
            "lord": fifth_lord_name,
            "occupants": occupants,
            "aspected_by": house_aspects,
        },
        "fifth_lord": (
            {
                "name": fifth_lord_name,
                "sign": fifth_lord.get("sign"),
                "house": fifth_lord.get("house"),
                "retrograde": fifth_lord.get("retrograde"),
                "conditions": conditions.get(fifth_lord_name, {}),
                "aspected_by": fifth_lord_aspects,
            }
            if fifth_lord
            else None
        ),
        "jupiter": (
            {
                "sign": jupiter.get("sign"),
                "house": jupiter.get("house"),
                "retrograde": jupiter.get("retrograde"),
                "conditions": conditions.get("Jupiter", {}),
            }
            if jupiter
            else None
        ),
    }


def summarize_siblings_context(kundli: Dict[str, Any]) -> Dict[str, Any]:
    house_lords = (kundli.get("yoga_analysis", {}) or {}).get("house_lords", {})
    planets = {
        planet.get("name"): planet
        for planet in kundli.get("planets", [])
        if "error" not in planet
    }
    vedic_aspects = kundli.get("vedic_aspects", {})

    def build_house_summary(house_no: int) -> Dict[str, Any]:
        house = house_lords.get(str(house_no), {})
        lord_name = house.get("lord")
        lord = planets.get(lord_name) if lord_name else None
        occupants = sorted(
            [
                planet.get("name")
                for planet in kundli.get("planets", [])
                if "error" not in planet and planet.get("house") == house_no
            ]
        )
        aspected_by = [
            {
                "from": aspect.get("from"),
                "aspect_name": aspect.get("aspect_name"),
                "aspect_type": aspect.get("aspect_type"),
            }
            for aspect in vedic_aspects.get("house_aspects", [])
            if aspect.get("to_house") == house_no
        ]
        lord_aspected_by = [
            {
                "from": aspect.get("from"),
                "aspect_name": aspect.get("aspect_name"),
                "aspect_type": aspect.get("aspect_type"),
            }
            for aspect in vedic_aspects.get("planet_to_planet", [])
            if aspect.get("to") == lord_name
        ]
        return {
            "house": house_no,
            "sign": house.get("sign"),
            "lord": lord_name,
            "occupants": occupants,
            "aspected_by": aspected_by,
            "lord_placement": (
                {
                    "name": lord_name,
                    "sign": lord.get("sign"),
                    "house": lord.get("house"),
                    "retrograde": lord.get("retrograde"),
                    "aspected_by": lord_aspected_by,
                }
                if lord
                else None
            ),
        }

    return {
        "younger_siblings": build_house_summary(3),
        "elder_siblings": build_house_summary(11),
        "karakas": {
            "Mercury": (
                {
                    "sign": planets["Mercury"].get("sign"),
                    "house": planets["Mercury"].get("house"),
                }
                if "Mercury" in planets else None
            ),
            "Mars": (
                {
                    "sign": planets["Mars"].get("sign"),
                    "house": planets["Mars"].get("house"),
                }
                if "Mars" in planets else None
            ),
        },
    }


def summarize_divisional_chart(
    kundli: Dict[str, Any],
    chart_code: str,
    key_planets: list[str],
    focal_house: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    divisional = (kundli.get("divisional_charts") or {}).get(chart_code)
    if not divisional:
        return None

    planets = {
        planet.get("name"): planet
        for planet in divisional.get("planets", [])
        if "error" not in planet
    }

    summary = {
        "chart": divisional.get("chart"),
        "name": divisional.get("name"),
        "purpose": divisional.get("purpose"),
        "ascendant": divisional.get("ascendant"),
        "key_planets": [
            {
                "name": name,
                "sign": planets[name].get("sign"),
                "house": planets[name].get("house"),
                "retrograde": planets[name].get("retrograde"),
                "source_sign": planets[name].get("source_sign"),
                "source_house": planets[name].get("source_house"),
            }
            for name in key_planets
            if name in planets
        ],
    }
    if focal_house:
        summary["focal_house"] = (divisional.get("house_lords") or {}).get(str(focal_house))
    return summary


def derive_ketu_context(kundli: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rahu = next(
        (
            planet
            for planet in kundli.get("planets", [])
            if planet.get("name") in {"TrueNode", "MeanNode"} and "error" not in planet
        ),
        None,
    )
    if not rahu:
        return None

    ketu_house = ((int(rahu["house"]) + 5) % 12) + 1
    ketu_sign_index = ((int(rahu["sign_index"]) + 5) % 12) + 1

    return {
        "name": "Ketu",
        "derived_from": rahu["name"],
        "placement_sign_index": ketu_sign_index,
        "placement_sign": ZODIAC_SIGNS[ketu_sign_index - 1],
        "placement_house": ketu_house,
    }


def get_dasha_lord_context(kundli: Dict[str, Any], planet_name: Optional[str]) -> Optional[Dict[str, Any]]:
    if not planet_name:
        return None
    if planet_name == "Ketu":
        return derive_ketu_context(kundli)
    if planet_name == "Rahu":
        return next(
            (
                {
                    "name": "Rahu",
                    "placement_sign": planet["sign"],
                    "placement_house": planet["house"],
                    "retrograde": planet["retrograde"],
                }
                for planet in kundli.get("planets", [])
                if planet.get("name") in {"TrueNode", "MeanNode"} and "error" not in planet
            ),
            None,
        )
    return next(
        (
            {
                "name": planet["name"],
                "placement_sign": planet["sign"],
                "placement_house": planet["house"],
                "retrograde": planet["retrograde"],
            }
            for planet in kundli.get("planets", [])
            if planet.get("name") == planet_name and "error" not in planet
        ),
        None,
    )


def canonical_planet_name(name: Optional[str]) -> str:
    if name in {"TrueNode", "MeanNode"}:
        return "Rahu"
    return str(name or "")


def format_date_short(value: Optional[str]) -> str:
    if not value:
        return "unknown"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d")
    except ValueError:
        return str(value)


def format_date_range(start: Optional[str], end: Optional[str]) -> str:
    return f"{format_date_short(start)} to {format_date_short(end)}"


def normalize_yoga_name(name: str) -> str:
    return " ".join(part.capitalize() for part in str(name or "").replace("_", " ").split())


def build_planet_lookup(kundli: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for planet in kundli.get("planets", []):
        if "error" in planet:
            continue
        canonical_name = canonical_planet_name(planet.get("name"))
        enriched = dict(planet)
        enriched["_canonical_name"] = canonical_name
        lookup[canonical_name] = enriched

    ketu_context = derive_ketu_context(kundli)
    if ketu_context:
        lookup["Ketu"] = {
            "name": "Ketu",
            "_canonical_name": "Ketu",
            "sign": ketu_context.get("placement_sign"),
            "house": ketu_context.get("placement_house"),
            "retrograde": True,
        }
    return lookup


def build_condition_tags(planet_name: str, kundli: Dict[str, Any], planet: Dict[str, Any]) -> list[str]:
    conditions = (kundli.get("planetary_conditions") or {}).get(planet_name) or planet.get("conditions") or {}
    tags: list[str] = []

    dignity = conditions.get("dignity") or {}
    dignity_status = dignity.get("status")
    if dignity_status and dignity_status not in {"ordinary", "not_applicable"}:
        tags.append(dignity_status.replace("_", " "))

    combustion = conditions.get("combustion") or {}
    if combustion.get("status") == "combust":
        tags.append("combust")

    functional = conditions.get("functional_nature") or {}
    functional_status = functional.get("status")
    if functional_status and functional_status not in {"ordinary", "mixed", "not_applicable"}:
        tags.append(functional_status.replace("_", " "))

    if planet.get("retrograde"):
        tags.append("retrograde")

    return tags


def summarize_planet_line(planet_name: str, kundli: Dict[str, Any], planet: Dict[str, Any]) -> str:
    sign = planet.get("sign", "Unknown sign")
    house = planet.get("house", "?")
    nakshatra = (planet.get("nakshatra") or {}).get("name")
    pada = (planet.get("nakshatra") or {}).get("pada")
    tags = build_condition_tags(planet_name, kundli, planet)
    tag_text = f" [{'; '.join(tags)}]" if tags else ""
    nakshatra_text = f", {nakshatra} pada {pada}" if nakshatra and pada else (f", {nakshatra}" if nakshatra else "")
    return f"- {planet_name}: {sign} {house}H{nakshatra_text}{tag_text}."


def summarize_house_lord_lines(kundli: Dict[str, Any], planet_lookup: Dict[str, Dict[str, Any]]) -> list[str]:
    house_lords = (kundli.get("yoga_analysis") or {}).get("house_lords") or {}
    entries: list[str] = []
    for house_no in range(1, 13):
        house_info = house_lords.get(str(house_no), {})
        lord_name = canonical_planet_name(house_info.get("lord"))
        lord = planet_lookup.get(lord_name)
        if lord:
            entries.append(f"{house_no}L {lord_name}->{lord.get('sign')} {lord.get('house')}H")
        elif lord_name:
            entries.append(f"{house_no}L {lord_name}")

    lines: list[str] = []
    chunk_size = 4
    for idx in range(0, len(entries), chunk_size):
        lines.append("- " + "; ".join(entries[idx: idx + chunk_size]) + ".")
    return lines


def summarize_yogas(kundli: Dict[str, Any]) -> str:
    yoga_analysis = kundli.get("yoga_analysis") or {}
    detected = [normalize_yoga_name(name) for name in yoga_analysis.get("detected", [])]
    conditional = [normalize_yoga_name(name) for name in yoga_analysis.get("conditional_detected", [])]

    parts = []
    if detected:
        parts.append(f"Present: {', '.join(detected)}")
    if conditional:
        parts.append(f"Conditional: {', '.join(conditional)}")
    return "; ".join(parts) if parts else "No major named yoga flagged strongly in the computed analysis."


def summarize_dasha_timeline(kundli: Dict[str, Any]) -> tuple[str, str]:
    current_dasha = kundli.get("current_dasha") or {}
    maha = current_dasha.get("mahadasha") or {}
    antara = current_dasha.get("antardasha") or {}
    pratya = current_dasha.get("pratyantardasha") or {}

    current_line = (
        f"{maha.get('planet', 'Unknown')} Mahadasha ({format_date_range(maha.get('start'), maha.get('end'))})"
    )
    if antara.get("planet"):
        current_line += (
            f" > {antara.get('planet')} Antardasha "
            f"({format_date_range(antara.get('start'), antara.get('end'))})"
        )
    if pratya.get("planet"):
        current_line += (
            f" > {pratya.get('planet')} Pratyantardasha "
            f"({format_date_range(pratya.get('start'), pratya.get('end'))})"
        )

    upcoming_parts: list[str] = []
    current_maha = next(
        (
            maha_entry
            for maha_entry in kundli.get("vimshottari_dasha", {}).get("mahadashas", [])
            if maha_entry.get("is_current")
        ),
        None,
    )
    if current_maha:
        antardashas = current_maha.get("antardashas", [])
        current_antardasha_idx = next(
            (idx for idx, entry in enumerate(antardashas) if entry.get("is_current")),
            None,
        )
        if current_antardasha_idx is not None:
            for entry in antardashas[current_antardasha_idx + 1: current_antardasha_idx + 3]:
                upcoming_parts.append(
                    f"{current_maha.get('planet')} > {entry.get('planet')} ({format_date_range(entry.get('start'), entry.get('end'))})"
                )

    next_maha = find_next_mahadasha(kundli)
    if next_maha:
        upcoming_parts.append(
            f"{next_maha.get('planet')} Mahadasha ({format_date_range(next_maha.get('start'), next_maha.get('end'))})"
        )

    return current_line, "; ".join(upcoming_parts) if upcoming_parts else "No later period data available."


def summarize_divisional_notes(kundli: Dict[str, Any]) -> list[str]:
    notes: list[str] = []
    divisional_charts = kundli.get("divisional_charts") or {}

    for chart_code, focal_house, focus_planets in [
        ("D9", 7, ["Sun", "Venus", "Jupiter"]),
        ("D10", 10, ["Sun", "Mercury", "Saturn"]),
    ]:
        chart = divisional_charts.get(chart_code)
        if not chart:
            continue

        planets = {
            canonical_planet_name(planet.get("name")): planet
            for planet in chart.get("planets", [])
            if "error" not in planet
        }
        asc_sign = (chart.get("ascendant") or {}).get("sign", "Unknown")
        focal = (chart.get("house_lords") or {}).get(str(focal_house), {})
        focal_lord = canonical_planet_name(focal.get("lord"))
        focal_placement = planets.get(focal_lord)

        highlight_bits = [f"ascendant {asc_sign}"]
        if focal_lord and focal_placement:
            highlight_bits.append(
                f"{focal_house}H lord {focal_lord} in {focal_placement.get('sign')} {focal_placement.get('house')}H"
            )

        for name in focus_planets:
            placement = planets.get(name)
            if placement:
                highlight_bits.append(f"{name} in {placement.get('sign')} {placement.get('house')}H")

        notes.append(f"- {chart_code}: " + "; ".join(highlight_bits) + ".")

    return notes


def summarize_aspect_notes(kundli: Dict[str, Any]) -> list[str]:
    aspect_data = (kundli.get("vedic_aspects") or {}).get("by_planet") or {}
    lines: list[str] = []

    for name in ["Mars", "Jupiter", "Saturn", "Rahu", "Ketu"]:
        source_key = "TrueNode" if name == "Rahu" and "TrueNode" in aspect_data else name
        planet_aspects = aspect_data.get(source_key)
        if not planet_aspects:
            continue

        snippets = []
        for aspect in planet_aspects.get("aspects", [])[:3]:
            target = f"{aspect.get('target_house')}H {aspect.get('target_sign')}"
            target_planets = aspect.get("target_planets") or []
            if target_planets:
                target += f" ({', '.join(target_planets)})"
            snippets.append(target)

        if snippets:
            lines.append(f"- {name} aspects " + "; ".join(snippets) + ".")

    return lines


def build_detailed_chart_summary(kundli: Dict[str, Any], profile: Optional[Dict[str, Any]] = None) -> str:
    profile = profile or {}
    planet_lookup = build_planet_lookup(kundli)
    ascendant = kundli.get("ascendant") or {}
    asc_sign = ascendant.get("sign", "Unknown")
    asc_ruler = SIGN_RULERS.get(asc_sign, "Unknown")
    asc_keywords = SIGN_KEYWORDS.get(asc_sign, "mixed")
    janma = kundli.get("janma_nakshatra") or {}
    current_line, upcoming_line = summarize_dasha_timeline(kundli)

    lines = ["CHART SUMMARY"]

    if profile.get("full_name"):
        lines.append(f"Native: {profile.get('full_name')}")

    birth_context = kundli.get("input") or {}
    local_datetime = birth_context.get("local_datetime")
    timezone_name = birth_context.get("timezone")
    if local_datetime or timezone_name:
        birth_line = "Birth context: "
        if local_datetime:
            birth_line += str(local_datetime)
        if timezone_name:
            birth_line += f" ({timezone_name})" if local_datetime else str(timezone_name)
        lines.append(birth_line)

    lines.append(f"Lagna: {asc_sign} ({asc_ruler}-ruled) — {asc_keywords}.")
    if janma.get("name"):
        lines.append(
            f"Janma Nakshatra: {janma.get('name')} pada {janma.get('pada')} ({janma.get('lord')}-ruled)."
        )

    lines.append("Planetary placements:")
    for planet_name in PLANET_DISPLAY_ORDER:
        planet = planet_lookup.get(planet_name)
        if planet:
            lines.append(summarize_planet_line(planet_name, kundli, planet))

    house_lord_lines = summarize_house_lord_lines(kundli, planet_lookup)
    if house_lord_lines:
        lines.append("House lord map:")
        lines.extend(house_lord_lines)

    lines.append(f"Active yogas: {summarize_yogas(kundli)}")
    lines.append(f"Current period: {current_line}")
    lines.append(f"Upcoming periods: {upcoming_line}")

    divisional_notes = summarize_divisional_notes(kundli)
    if divisional_notes:
        lines.append("Divisional notes:")
        lines.extend(divisional_notes)

    aspect_notes = summarize_aspect_notes(kundli)
    if aspect_notes:
        lines.append("Aspect highlights:")
        lines.extend(aspect_notes)

    return "\n".join(lines)


def derive_ketu_from_chart_data(chart_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rahu = next(
        (
            planet
            for planet in chart_data.get("planets", [])
            if planet.get("name") in {"TrueNode", "MeanNode", "Rahu"} and "error" not in planet
        ),
        None,
    )
    if not rahu:
        return None

    ketu_house = ((int(rahu["house"]) + 5) % 12) + 1
    sign_index = int(rahu.get("sign_index", 0) or 0)
    ketu_sign_index = ((sign_index + 5) % 12) + 1 if sign_index else None

    return {
        "name": "Ketu",
        "house": ketu_house,
        "sign": ZODIAC_SIGNS[ketu_sign_index - 1] if ketu_sign_index else "Unknown",
        "sign_index": ketu_sign_index,
        "degree_in_sign": rahu.get("degree_in_sign"),
        "retrograde": True,
        "source_sign": (
            ZODIAC_SIGNS[(ZODIAC_SIGNS.index(rahu["source_sign"]) + 6) % 12]
            if rahu.get("source_sign") in ZODIAC_SIGNS
            else None
        ),
        "source_house": (((int(rahu["source_house"]) + 5) % 12) + 1) if rahu.get("source_house") else None,
    }


def get_chart_data_for_code(kundli: Dict[str, Any], chart_code: str) -> Dict[str, Any]:
    if chart_code == "D1":
        return kundli
    chart = (kundli.get("divisional_charts") or {}).get(chart_code)
    if not chart:
        raise HTTPException(status_code=404, detail=f"{chart_code} chart is not available")
    return chart


def build_chart_planet_lookup(chart_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}

    for planet in chart_data.get("planets", []):
        if "error" in planet:
            continue
        canonical_name = canonical_planet_name(planet.get("name"))
        if canonical_name == "Rahu" and canonical_name in lookup:
            continue
        enriched = dict(planet)
        enriched["_canonical_name"] = canonical_name
        lookup[canonical_name] = enriched

    ketu = derive_ketu_from_chart_data(chart_data)
    if ketu:
        lookup["Ketu"] = ketu

    return lookup


def is_within_degree_range(value: float, start_deg: float, end_deg: float) -> bool:
    return start_deg <= value < end_deg or (end_deg == 30.0 and value <= end_deg)


def get_dignity_status(planet_name: str, sign_name: Optional[str], degree_in_sign: Optional[float]) -> Optional[str]:
    if planet_name not in EXALTATION_SIGNS or sign_name not in ZODIAC_SIGNS or degree_in_sign is None:
        return None

    degree_value = float(degree_in_sign)
    exaltation = EXALTATION_SIGNS[planet_name]
    debilitation = DEBILITATION_SIGNS[planet_name]
    moolatrikona = MOOLATRIKONA_RANGES[planet_name]

    if sign_name == exaltation["sign"]:
        return "exalted"
    if sign_name == debilitation["sign"]:
        return "debilitated"
    if sign_name == moolatrikona["sign"] and is_within_degree_range(
        degree_value,
        moolatrikona["start_deg"],
        moolatrikona["end_deg"],
    ):
        return "moolatrikona"
    if sign_name in OWN_SIGNS.get(planet_name, set()):
        return "own sign"
    return None


def get_chart_condition_data(kundli: Dict[str, Any], planet_name: str) -> Dict[str, Any]:
    conditions = kundli.get("planetary_conditions") or {}
    if planet_name in conditions:
        return conditions[planet_name] or {}
    if planet_name == "Rahu":
        return conditions.get("TrueNode") or conditions.get("MeanNode") or {}
    return {}


def get_chart_influence_label(
    kundli: Dict[str, Any],
    chart_code: str,
    planet_name: str,
    statuses: list[str],
) -> str:
    score = 0

    if "Exalted" in statuses:
        score += 2
    if "Own Sign" in statuses or "Moolatrikona" in statuses:
        score += 1
    if "Vargottama" in statuses:
        score += 1
    if "Debilitated" in statuses:
        score -= 2
    if "Combust" in statuses:
        score -= 1

    if chart_code == "D1":
        functional = (get_chart_condition_data(kundli, planet_name).get("functional_nature") or {}).get("status")
        if functional == "functional_benefic":
            score += 2
        elif functional == "functional_malefic":
            score -= 2

    if score >= 2:
        return "supportive"
    if score <= -2:
        return "challenging"
    return "mixed"


def build_chart_hover_summary(
    kundli: Dict[str, Any],
    chart_code: str,
    planet_name: str,
    planet: Dict[str, Any],
    statuses: list[str],
    influence: str,
) -> str:
    sign = planet.get("sign", "Unknown")
    house = int(planet.get("house") or 0)
    planet_theme = PLANET_THEMES.get(planet_name, "core life themes")
    house_theme = HOUSE_THEMES.get(house, "important life areas")

    if influence == "supportive":
        tone_line = "This placement is broadly supportive and tends to help the native express this planet constructively."
    elif influence == "challenging":
        tone_line = "This placement is more challenging and may require conscious effort, maturity, or remedies to handle well."
    else:
        tone_line = "This placement is mixed, so results can be useful but tend to come with some complexity or fluctuation."

    status_line = ""
    if statuses:
        status_line = " Current signals: " + ", ".join(statuses).lower() + "."

    chart_context = {
        "D1": "In the natal chart,",
        "D9": "In the Navamsha,",
        "D10": "In the Dashamsha,",
    }.get(chart_code, "In this chart,")

    return (
        f"{planet_name} signifies {planet_theme}. "
        f"{chart_context} it works through {sign} in the {house} house, highlighting {house_theme}. "
        f"{tone_line}{status_line}"
    )


def is_vargottama_placement(
    planet_name: str,
    chart_code: str,
    sign_name: Optional[str],
    natal_lookup: Dict[str, Dict[str, Any]],
    d9_lookup: Dict[str, Dict[str, Any]],
) -> bool:
    if sign_name not in ZODIAC_SIGNS:
        return False

    if chart_code == "D1":
        return (d9_lookup.get(planet_name) or {}).get("sign") == sign_name
    if chart_code == "D9":
        return (natal_lookup.get(planet_name) or {}).get("sign") == sign_name
    return False


def build_chart_planet_details(kundli: Dict[str, Any], chart_code: str) -> list[Dict[str, Any]]:
    chart_data = get_chart_data_for_code(kundli, chart_code)
    chart_lookup = build_chart_planet_lookup(chart_data)
    natal_lookup = build_chart_planet_lookup(kundli)
    d9_lookup = build_chart_planet_lookup((kundli.get("divisional_charts") or {}).get("D9") or {})
    details: list[Dict[str, Any]] = []

    for planet_name in PLANET_DISPLAY_ORDER:
        planet = chart_lookup.get(planet_name)
        if not planet:
            continue

        statuses: list[str] = []
        dignity_status = get_dignity_status(
            planet_name,
            planet.get("sign"),
            planet.get("degree_in_sign"),
        )
        if dignity_status:
            statuses.append(dignity_status.title())

        if chart_code == "D1":
            combustion = (get_chart_condition_data(kundli, planet_name).get("combustion") or {})
            if combustion.get("status") == "combust":
                statuses.append("Combust")

        if planet.get("retrograde"):
            statuses.append("Retrograde")

        if is_vargottama_placement(
            planet_name,
            chart_code,
            planet.get("sign"),
            natal_lookup,
            d9_lookup,
        ):
            statuses.append("Vargottama")

        influence = get_chart_influence_label(kundli, chart_code, planet_name, statuses)
        hover_summary = build_chart_hover_summary(
            kundli,
            chart_code,
            planet_name,
            planet,
            statuses,
            influence,
        )

        details.append(
            {
                "name": planet_name,
                "short_name": PLANET_SHORT_SYMBOLS.get(planet_name, planet_name[:2]),
                "sign": planet.get("sign"),
                "house": planet.get("house"),
                "degree_in_sign": planet.get("degree_in_sign"),
                "retrograde": bool(planet.get("retrograde", False)),
                "source_sign": planet.get("source_sign"),
                "source_house": planet.get("source_house"),
                "statuses": statuses,
                "influence": influence,
                "hover_summary": hover_summary,
            }
        )

    details.sort(key=lambda item: PLANET_SORT_ORDER.get(item["name"], 999))
    return details


def build_chart_label_suffix(statuses: list[str]) -> str:
    suffix = ""
    if "Retrograde" in statuses:
        suffix += "*"
    if "Exalted" in statuses:
        suffix += "↑"
    elif "Debilitated" in statuses:
        suffix += "↓"
    return suffix


def add_svg_text_attr(open_tag: str, attr_name: str, attr_value: str) -> str:
    if f'{attr_name}="' in open_tag:
        return open_tag
    return open_tag[:-1] + f' {attr_name}="{attr_value}">'


def inject_chart_planet_markers(svg: str, details: list[Dict[str, Any]]) -> str:
    for detail in details:
        base_label = PLANET_SHORT_SYMBOLS.get(detail["name"], detail["name"][:2])
        suffix = build_chart_label_suffix(detail.get("statuses") or [])

        pattern = rf'(<text\b[^>]*class="[^"]*\bplanet\b[^"]*"[^>]*>)(?:\({re.escape(base_label)}\)|{re.escape(base_label)})(</text>)'
        def repl(match: re.Match[str]) -> str:
            open_tag = add_svg_text_attr(match.group(1), "data-planet", detail["name"])
            open_tag = add_svg_text_attr(open_tag, "data-short-name", base_label)
            return f"{open_tag}{base_label}{suffix}{match.group(2)}"

        svg = re.sub(pattern, repl, svg, count=1)

    return svg


def shift_sign_numbers_right(svg: str, shift_px: float = 6.0) -> str:
    def repl(match: re.Match[str]) -> str:
        x_value = float(match.group(1))
        return f'x="{x_value + shift_px:g}"'

    return re.sub(r'x="([0-9]+(?:\.[0-9]+)?)"(?=[^>]*class="sign-num")', repl, svg)


def prepare_planets_for_chart(chart_data: Dict[str, Any]) -> list[Dict[str, Any]]:
    planets = []
    rahu_added = False

    for planet in chart_data.get("planets", []):
        if "error" in planet:
            continue
        canonical_name = canonical_planet_name(planet.get("name"))
        if canonical_name == "Rahu":
            if rahu_added:
                continue
            rahu_added = True
        if canonical_name not in JYOTI_PLANETS or canonical_name == "Ketu":
            continue
        planets.append({
            "name": canonical_name,
            "house": int(planet["house"]),
            "retrograde": bool(planet.get("retrograde", False)),
        })

    ketu = derive_ketu_from_chart_data(chart_data)
    if ketu:
        planets.append({
            "name": "Ketu",
            "house": int(ketu["house"]),
            "retrograde": True,
        })

    return planets


def style_chart_object(chart: Any, style: str) -> None:
    house_fills = ["#0f172a"] * 12
    if style == "north":
        chart.updatechartcfg(
            aspect=False,
            clr_background="#020617",
            clr_outbox="#334155",
            clr_line="#64748b",
            clr_sign="#cbd5e1",
            clr_houses=house_fills,
        )
    else:
        chart.updatechartcfg(
            aspect=False,
            clr_background="#020617",
            clr_outbox="#334155",
            clr_inbox="#334155",
            clr_line="#64748b",
            clr_Asc="#cbd5e1",
            clr_houses=house_fills,
        )


def render_chart_svg(
    kundli: Dict[str, Any],
    chart_code: str,
    style: str,
    person_name: Optional[str] = None,
) -> str:
    chart_data = get_chart_data_for_code(kundli, chart_code)
    ascendant = chart_data.get("ascendant") or {}
    asc_sign = ascendant.get("sign")
    if not asc_sign:
        raise HTTPException(status_code=500, detail=f"{chart_code} chart is missing ascendant data")

    chart_title = CHART_OPTIONS.get(chart_code, {}).get("label", chart_code)
    safe_name = (person_name or "native").replace(" ", "_")

    if style == "north":
        chart_obj = NorthChart(chart_title, safe_name)
    elif style == "south":
        chart_obj = SouthChart(chart_title, safe_name)
    else:
        raise HTTPException(status_code=400, detail="Unsupported chart style")

    chart_obj.set_ascendantsign(asc_sign)
    style_chart_object(chart_obj, style)
    chart_details = build_chart_planet_details(kundli, chart_code)

    for planet in prepare_planets_for_chart(chart_data):
        chart_obj.add_planet(
            JYOTI_PLANETS[planet["name"]],
            PLANET_SHORT_SYMBOLS[planet["name"]],
            planet["house"],
            retrograde=planet["retrograde"],
            colour="#f8fafc",
        )

    with TemporaryDirectory() as temp_dir:
        file_name = f"{chart_code.lower()}_{style}"
        chart_obj.draw(temp_dir, file_name)
        svg_path = os.path.join(temp_dir, f"{file_name}.svg")
        with open(svg_path, "r", encoding="utf-16") as svg_file:
            svg = svg_file.read()

    svg = svg.replace(
        ".planet { font-size: 20px; font-weight: bold; font-family: sans-serif; }",
        ".planet { font-size: 16px; font-weight: bold; font-family: sans-serif; cursor: pointer; }"
        "\n    .planet-hover { transition: transform 140ms ease, fill 140ms ease; transform-box: fill-box; transform-origin: center; }"
        "\n    .planet-hover:hover { transform: scale(1.18); fill: #ffffff; }",
    )
    svg = svg.replace('class="planet"', 'class="planet planet-hover"')
    svg = svg.replace(".sign-num { font-size: 22px;", ".sign-num { font-size: 17px;")
    svg = svg.replace(' text-decoration="underline"', "")
    svg = re.sub(r'(<text[^>]*class="sign-num"[^>]*>)(0)([1-9])(<\/text>)', r"\1\3\4", svg)
    svg = shift_sign_numbers_right(svg)
    svg = inject_chart_planet_markers(svg, chart_details)

    return svg


async def get_or_restore_kundli(session_id: str) -> Optional[Dict[str, Any]]:
    kundli = get_kundli(session_id)
    if kundli:
        return kundli

    try:
        sessions_collection = get_sessions_collection()
        session_doc = await sessions_collection.find_one(
            {"session_id": session_id},
            {"birth_details": 1, "full_name": 1},
        )
    except Exception:
        logger.exception("Failed to load session data for chart restore")
        return None

    birth_details = (session_doc or {}).get("birth_details")
    if not birth_details:
        return None

    try:
        kundli = json.loads(generate_chart(birth_details, house_system="WS"))
    except Exception:
        logger.exception("Failed to regenerate kundli for session_id=%s", session_id)
        return None

    store_kundli(session_id, kundli)
    store_chart_summary(
        session_id,
        build_detailed_chart_summary(kundli, {"full_name": (session_doc or {}).get("full_name")}),
    )
    return kundli


def ensure_chart_summary_in_memory(chain: ConversationChain, chart_summary: str) -> None:
    if not chart_summary:
        return
    for message in chain.memory.chat_memory.messages:
        if isinstance(message, SystemMessage) and message.content.strip() == chart_summary.strip():
            return
    chain.memory.chat_memory.add_message(SystemMessage(content=chart_summary))


def build_inline_chart_prompt(
    chain: ConversationChain,
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


def build_prompt_kundli_context(kundli: Dict[str, Any], user_query: Optional[str] = None) -> Dict[str, Any]:
    query = (user_query or "").lower()
    wants_marriage = any(
        token in query
        for token in ["marriage", "spouse", "wife", "husband", "partner", "relationship", "love", "romance"]
    )
    wants_career = any(
        token in query
        for token in ["career", "profession", "job", "work", "business", "status", "promotion"]
    )
    wants_dasha = any(
        token in query
        for token in ["dasha", "mahadasha", "antardasha", "pratyantardasha", "next", "future", "when", "marriage", "career", "time"]
    )
    wants_yoga = any(
        token in query
        for token in ["yoga", "dosha", "manglik", "raj", "budhaditya", "gajakesari", "dhana", "kaal sarpa", "sade sati"]
    )
    wants_aspects = any(
        token in query
        for token in [
            "aspect", "aspects", "drishti",
            "relationship", "relationships", "partner", "spouse",
            "marriage", "love", "romance", "compatibility",
            "career", "profession", "job", "work", "business",
            "health",
        ]
    )
    wants_strength = any(
        token in query
        for token in [
            "exalted", "exaltation", "debilitated", "debilitation",
            "own sign", "moolatrikona", "combust", "combustion",
            "benefic", "malefic", "strong", "weak", "strength",
        ]
    )
    wants_children = any(
        token in query
        for token in [
            "child", "children", "kid", "kids", "offspring",
            "pregnancy", "conceive", "conception", "fertility",
            "son", "daughter",
        ]
    )
    wants_siblings = any(
        token in query
        for token in ["sibling", "siblings", "brother", "brothers", "sister", "sisters"]
    )

    current_dasha = kundli.get("current_dasha", {})
    next_mahadasha = find_next_mahadasha(kundli)
    yoga_analysis = kundli.get("yoga_analysis", {})
    yoga_details = {
        key: value
        for key, value in yoga_analysis.items()
        if key not in {"house_lords"}
    }

    context = {
        "ascendant": kundli.get("ascendant"),
        "janma_nakshatra": kundli.get("janma_nakshatra"),
        "question_focus": infer_question_focus(user_query),
        "key_planets": summarize_planets(
            kundli,
            ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "TrueNode"],
        ),
    }

    if wants_dasha or not wants_yoga:
        context["current_dasha"] = current_dasha
        context["next_mahadasha"] = next_mahadasha
        context["current_mahadasha_lord_context"] = get_dasha_lord_context(
            kundli,
            current_dasha.get("mahadasha", {}).get("planet"),
        )
        context["next_mahadasha_lord_context"] = get_dasha_lord_context(
            kundli,
            next_mahadasha.get("planet") if next_mahadasha else None,
        )
        context["mahadasha_timeline"] = [
            {
                "planet": maha.get("planet"),
                "start": maha.get("start"),
                "end": maha.get("end"),
                "is_current": maha.get("is_current", False),
            }
            for maha in kundli.get("vimshottari_dasha", {}).get("mahadashas", [])
        ]
        if next_mahadasha:
            context["next_mahadasha_antardashas"] = next_mahadasha.get("antardashas", [])

    if wants_yoga or not wants_dasha:
        context["yoga_analysis"] = yoga_details

    if wants_aspects:
        context["vedic_aspects"] = summarize_vedic_aspects(
            kundli,
            ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"],
        )

    if wants_strength:
        context["planetary_conditions"] = summarize_planetary_conditions(
            kundli,
            ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"],
            user_query=user_query,
        )

    if wants_children:
        context["children_analysis"] = summarize_children_context(kundli)

    if wants_siblings:
        context["siblings_analysis"] = summarize_siblings_context(kundli)

    if wants_marriage:
        context["navamsha_d9"] = summarize_divisional_chart(
            kundli,
            "D9",
            ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "TrueNode"],
            focal_house="7",
        )

    if wants_career:
        context["dashamsha_d10"] = summarize_divisional_chart(
            kundli,
            "D10",
            ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "TrueNode"],
            focal_house="10",
        )

    return context


def build_first_message_context(kundli: Dict[str, Any], profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    profile = profile or {}
    yoga_analysis = kundli.get("yoga_analysis", {})
    strong_yogas = list(yoga_analysis.get("detected", []))
    conditional_yogas = list(yoga_analysis.get("conditional_detected", []))

    return {
        "name": profile.get("full_name"),
        "first_name": get_first_name(profile.get("full_name")),
        "birth_context": {
            "local_datetime": kundli.get("input", {}).get("local_datetime"),
            "timezone": kundli.get("input", {}).get("timezone"),
            "latitude": kundli.get("input", {}).get("latitude"),
            "longitude": kundli.get("input", {}).get("longitude"),
        },
        "ascendant": kundli.get("ascendant"),
        "janma_nakshatra": kundli.get("janma_nakshatra"),
        "current_dasha": kundli.get("current_dasha"),
        "key_planets": summarize_planets(
            kundli,
            ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "TrueNode"],
        ),
        "strong_yogas": {
            key: yoga_analysis.get(key)
            for key in strong_yogas
        },
        "conditional_yogas": {
            key: yoga_analysis.get(key)
            for key in conditional_yogas
        },
    }


def create_chain_for_session(session_id: str) -> ConversationChain:
    memory = ConversationBufferMemory(llm=llm, return_messages=True, max_token_limit=800)
    chain = ConversationChain(llm=llm, memory=memory, verbose=False)
    logger.info("create_chain_for_session: created chain id=%s for session_id=%s", id(chain), session_id)
    return chain

def get_or_create_chain(session_id: str) -> ConversationChain:
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

# To lot the metadata of each request for debugging
# @app.middleware("http")
# async def log_headers(request: Request, call_next):
#     sid = request.headers.get("x-session-id")
#     logger.info("REQ path=%s pid=%s X-Session-Id=%s", request.url.path, os.getpid(), sid)
#     return await call_next(request)


# ----- Helper to build the LLM prompt summary for kundli -----
def build_kundli_prompt(kundli: Dict[str, Any], profile: Optional[Dict[str, Any]], today: datetime) -> str:
    response_style = build_response_style_instructions(is_first_message=True)
    reasoning_framework = build_astrology_reasoning_framework(is_first_message=True)
    chart_summary = build_detailed_chart_summary(kundli, profile)
    core_rules = (
        "You are writing the very first message inside Nakshatra AI after a user submits birth details.\n"
        "You are a master Vedic astrologer (Jyotishi) with decades of practice. Use only the provided chart data. Do not use western terminology.\n\n"
        "### Core Rules\n"
        "1. NEVER ask for birth details. They are already available.\n"
        "2. DO NOT recalculate Mahadasha or Antardasha. Use the given data only.\n"
        "3. This message should feel premium, insightful, human, and welcoming, not like a raw placement dump.\n"
        "4. Focus on what is special about the chart: baseline nature, hidden emotional layer, promise/potential, and the current dasha chapter.\n"
        "5. Mention only 3 to 4 chart signatures that are genuinely the most compelling.\n"
        "6. If a yoga is strong, present it confidently in plain language. If a yoga is conditional, mention it only with nuance.\n"
        "7. Use crisp, premium Markdown formatting with bold headers and tasteful emojis. No tables.\n"
        "8. End with one warm, concise prompt inviting the user to choose one of: career, relationships, or deeper purpose.\n"
        "9. Follow the response mode instructions exactly for length and depth.\n\n"
        "### Output Format (must follow this structure)\n"
        "## 🌌 Welcome to your Nakshatra AI reading, {first_name}\n"
        "A short 2-sentence opening that captures the user's chart essence.\n"
        "### ✨ **What stands out in your chart**\n"
        "One short paragraph.\n"
        "### 🌙 **Your hidden strength**\n"
        "One short paragraph.\n"
        "### 💠 **The promise in this chart**\n"
        "One short paragraph.\n"
        "### 🔮 **Your current chapter**\n"
        "One short paragraph using the current dasha.\n"
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

    prompt = f"""{core_rules}
{reasoning_framework}
{response_style}

### User Profile
{json.dumps({"full_name": (profile or {}).get("full_name"), "first_name": get_first_name((profile or {}).get("full_name"))}, indent=2)}

### Chart Context
{chart_summary}

### Today's Context
Date: {today.strftime('%Y-%m-%d')}
"""
    return prompt



def prune_memory_keep_last(chain: ConversationChain, keep_last_pairs: int = 1):
    msgs = chain.memory.chat_memory.messages
    if msgs:
        system_msgs = [msg for msg in msgs if isinstance(msg, SystemMessage)]
        conversation_msgs = [msg for msg in msgs if not isinstance(msg, SystemMessage)]
        chain.memory.chat_memory.messages = system_msgs + conversation_msgs[-(keep_last_pairs*2):]
# ----- Endpoints -----


@app.post("/kundli")
async def kundli(request: Request):
    """
    Generate & store kundli for a session.
    Expects a JSON body with the birth details required by generate_chart.
    Session id is read from header 'X-Session-Id' (fallback to 'default').
    """
    session_id = request.headers.get("x-session-id")
    if not session_id:
        logger.warning("Missing X-Session-Id header")
        raise HTTPException(status_code=400, detail="Missing X-Session-Id header")
    
    try:
        payload = await request.json()
        print("This is the payload",payload)
    except Exception:
        logger.exception("Invalid JSON in /kundli")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Generate the kundli (your generate_chart or get_kundli_data wrapper)
    try:
        kundli = json.loads(generate_chart(payload, house_system="WS"))
    except Exception:
        logger.exception("Failed to generate kundli")
        raise HTTPException(status_code=500, detail="Failed to generate kundli")

    # Store kundli per session (in memory)
    store_kundli(session_id, kundli)
    logger.info("Stored kundli for session_id=%s", session_id)
    chart_summary = build_detailed_chart_summary(kundli, {"full_name": payload.get("fullName")})
    store_chart_summary(session_id, chart_summary)
    
    # Store session data in MongoDB
    try:
        sessions_collection = get_sessions_collection()
        full_name = payload.get("fullName", "Unknown")
        
        logger.info("Attempting to save kundli data: full_name=%s, session_id=%s", full_name, session_id)
        
        # Check if session already exists
        existing_session = await sessions_collection.find_one({"session_id": session_id})
        
        if existing_session:
            # Update existing session with birth data (not kundli result)
            result = await sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {
                    "full_name": full_name,
                    "birth_details": payload,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            logger.info("Updated session with birth data for session_id=%s, matched=%s, modified=%s", 
                       session_id, result.matched_count, result.modified_count)
        else:
            # Create new session document (without kundli result)
            session_doc = SessionData(
                session_id=session_id,
                full_name=full_name,
                birth_details=payload,
            )
            result = await sessions_collection.insert_one(session_doc.dict())
            logger.info("Created new session with birth data for session_id=%s, inserted_id=%s", 
                       session_id, result.inserted_id)
    except Exception as e:
        logger.exception("Failed to save session data to MongoDB (non-fatal): %s", e)

    # Create or get the conversation chain for this session and add kundli as a system message in its memory
    chain = get_or_create_chain(session_id)
    try:
        ensure_chart_summary_in_memory(chain, chart_summary)
    except Exception:
        # memory addition is not critical; log and continue
        logger.exception("Failed to add kundli to session memory (non-fatal)")

    # Optionally produce a short LLM summary of the kundli to return to the frontend
    try:
        prompt = build_kundli_prompt(
            kundli,
            {"full_name": payload.get("fullName")},
            datetime.now(),
        )
        llm_resp = llm.invoke(prompt)
        summary_text = getattr(llm_resp, "content", str(llm_resp)).strip()
        summary_text = complete_if_truncated(summary_text)
    except Exception:
        logger.exception("LLM invoke failed for kundli summary; returning kundli without summary")
        summary_text = None

    return JSONResponse(content={"response": summary_text or "Kundli generated successfully."})


@app.get("/charts")
async def charts(request: Request):
    session_id = request.headers.get("x-session-id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-Id header")

    chart_code = (request.query_params.get("code") or "D1").upper()
    style = (request.query_params.get("style") or "south").lower()

    if chart_code not in CHART_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported chart code: {chart_code}")
    if style not in CHART_STYLES:
        raise HTTPException(status_code=400, detail=f"Unsupported chart style: {style}")

    kundli = await get_or_restore_kundli(session_id)
    if not kundli:
        raise HTTPException(status_code=404, detail="Kundli not found for this session")

    try:
        chart_data = get_chart_data_for_code(kundli, chart_code)
        svg = render_chart_svg(
            kundli,
            chart_code=chart_code,
            style=style,
            person_name=session_id,
        )
        details = build_chart_planet_details(kundli, chart_code)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to render chart SVG for session_id=%s", session_id)
        raise HTTPException(status_code=500, detail="Failed to render chart")

    return JSONResponse(
        content={
            "chart_code": chart_code,
            "chart_label": CHART_OPTIONS[chart_code]["label"],
            "style": style,
            "svg": svg,
            "ascendant": chart_data.get("ascendant") or {},
            "details": details,
        }
    )


@app.post("/chat")
async def chat(request: Request):
    """
    Chat endpoint:
    - Reads session id from header X-Session-Id (fallback 'default')
    - Looks up kundli for that session and appends it to the input prompt (if present)
    - Uses a per-session ConversationChain to keep chats isolated
    """
    session_id = request.headers.get("x-session-id", "default")

    try:
        payload = await request.json()
    except Exception:
        logger.exception("Invalid JSON in /chat")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    user_query = payload.get("query")
    if not user_query:
        raise HTTPException(status_code=400, detail="Missing 'query' in payload")

    logger.info("Received chat (session=%s): %s", session_id, user_query)

    # get or create chain for session
    chain = get_or_create_chain(session_id)
    
    # Save user message to MongoDB
    try:
        sessions_collection = get_sessions_collection()
        user_message = Message(
            role="user",
            message=user_query
        )
        
        # Upsert: update if exists, create if doesn't
        await sessions_collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": user_message.dict()},
                "$set": {"updated_at": datetime.now(timezone.utc)},
                "$setOnInsert": {
                    "session_id": session_id,
                    "created_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        logger.info("Saved user message to MongoDB for session_id=%s", session_id)
    except Exception as e:
        logger.exception("Failed to save user message to MongoDB (non-fatal): %s", e)

    # Attach preserved chart summary as system context when available.
    kundli = get_kundli(session_id)
    chart_summary = get_chart_summary(session_id)
    if kundli:
        if not chart_summary:
            chart_summary = build_detailed_chart_summary(kundli)
            store_chart_summary(session_id, chart_summary)
        ensure_chart_summary_in_memory(chain, chart_summary)
        response_style = build_response_style_instructions(user_query=user_query)
        final_input = (
            "You are a seasoned Vedic astrologer (Jyotishi).\n"
            "Use only the chart summary and recent conversation below.\n"
            "Do not invent chart facts, yogas, dates, or remedies.\n"
            "Answer directly and support your conclusions with the most relevant placements, house lords, yogas, aspects, dashas, or divisional-chart notes.\n"
            "If the chart is mixed, say so clearly.\n"
            "If asked about death prediction or exact death timing, refuse briefly and redirect to safer guidance.\n"
            "Use readable Markdown and no tables.\n\n"
            f"{response_style}\n"
            f"User Query: {user_query}"
        )
    else:
        final_input = user_query
    prune_memory_keep_last(chain, keep_last_pairs=1)
    # run the conversation chain
    try:
        prompt_payload = build_inline_chart_prompt(chain, chart_summary if kundli else None, final_input)
        llm_resp = llm.invoke(prompt_payload)
        resp_text = getattr(llm_resp, "content", str(llm_resp)).strip()
        if not resp_text:
            retry_resp = llm.invoke(prompt_payload)
            resp_text = getattr(retry_resp, "content", str(retry_resp)).strip()
        if not resp_text:
            raise ValueError("Empty response from LLM")
        resp_text = complete_if_truncated(resp_text)
        chain.memory.chat_memory.add_user_message(user_query)
        chain.memory.chat_memory.add_ai_message(resp_text)
        prune_memory_keep_last(chain, keep_last_pairs=1)
    except Exception:
        logger.exception("ConversationChain failed for session %s", session_id)
        raise HTTPException(status_code=500, detail="LLM conversation failed")
    
    # Save assistant response to MongoDB
    try:
        sessions_collection = get_sessions_collection()
        assistant_message = Message(
            role="assistant",
            message=resp_text
        )
        
        await sessions_collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": assistant_message.dict()},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        logger.info("Saved assistant message to MongoDB for session_id=%s", session_id)
    except Exception as e:
        logger.exception("Failed to save assistant message to MongoDB (non-fatal): %s", e)

    return JSONResponse(content={"response": resp_text})

# Only for local testing; use uvicorn command line in production
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

# uvicorn main:app --host 0.0.0.0 --port 8000 --reload    

# Windows
# .\venv\Scripts\Activate.ps1  

# Mac
# python3 -m venv venv
# source venv/bin/activate
