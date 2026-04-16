import os
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from threading import Lock
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage

# from api.astrology import get_kundli_data // Can use freeastrologyapi.com to get kundli data
from astro.astro import generate_chart
from database import connect_to_mongo, close_mongo_connection, get_sessions_collection
from models import SessionData, Message

# ----- Logging -----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nakshatra-backend")

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

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


def store_kundli(session_id: str, kundli: Dict[str, Any]) -> None:
    with _kundli_lock:
        _kundli_store[session_id] = kundli


def get_kundli(session_id: str) -> Optional[Dict[str, Any]]:
    with _kundli_lock:
        return _kundli_store.get(session_id)


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

    if any(token in query for token in ["marriage", "spouse", "wife", "husband", "partner", "relationship", "love", "romance"]):
        topic = "marriage_relationships"
        relevant_houses = [1, 5, 7, 8, 12]
        relevant_karakas = ["Venus", "Jupiter", "Moon", "7th lord"]
        supporting_charts = ["D9"]
        remedies_relevant = True
        timing_focus = True
    elif any(token in query for token in ["career", "profession", "job", "work", "business", "promotion", "status"]):
        topic = "career"
        relevant_houses = [1, 2, 6, 10, 11]
        relevant_karakas = ["Sun", "Saturn", "Mercury", "10th lord"]
        supporting_charts = ["D10"]
        remedies_relevant = True
        timing_focus = True
    elif any(token in query for token in ["child", "children", "kid", "kids", "offspring", "pregnancy", "fertility", "son", "daughter"]):
        topic = "children"
        relevant_houses = [2, 5, 9, 11]
        relevant_karakas = ["Jupiter", "Moon", "5th lord"]
        remedies_relevant = True
    elif any(token in query for token in ["sibling", "siblings", "brother", "brothers", "sister", "sisters"]):
        topic = "siblings"
        relevant_houses = [3, 11]
        relevant_karakas = ["Mercury", "Mars", "3rd lord", "11th lord"]
    elif any(token in query for token in ["money", "wealth", "finance", "income", "rich", "prosperity"]):
        topic = "wealth"
        relevant_houses = [2, 5, 9, 11]
        relevant_karakas = ["Jupiter", "Venus", "2nd lord", "11th lord"]
        remedies_relevant = True
    elif any(token in query for token in ["health", "disease", "illness", "body", "hospital"]):
        topic = "health"
        relevant_houses = [1, 6, 8, 12]
        relevant_karakas = ["Sun", "Moon", "Mars", "Saturn", "6th lord"]
        remedies_relevant = True
    elif any(token in query for token in ["sensual", "sexual", "intimacy", "passion"]):
        topic = "sensuality_intimacy"
        relevant_houses = [1, 5, 7, 8, 12]
        relevant_karakas = ["Venus", "Mars", "Moon"]
        supporting_charts = ["D9"]
    elif any(token in query for token in ["death", "longevity", "end of life"]):
        topic = "longevity_sensitive"
        relevant_houses = [1, 3, 8]
        relevant_karakas = ["Saturn", "8th lord"]

    return {
        "topic": topic,
        "relevant_houses": relevant_houses,
        "relevant_karakas": relevant_karakas,
        "supporting_charts": supporting_charts,
        "timing_focus": timing_focus,
        "remedies_relevant": remedies_relevant,
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
        f"9. Topic metadata: {json.dumps(focus, ensure_ascii=False)}\n"
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
{json.dumps(build_first_message_context(kundli, profile), indent=2)}

### Today's Context
Date: {today.strftime('%Y-%m-%d')}
"""
    return prompt



def prune_memory_keep_last(chain: ConversationChain, keep_last_pairs: int = 1):
    msgs = chain.memory.chat_memory.messages
    if msgs:
        chain.memory.chat_memory.messages = msgs[-(keep_last_pairs*2):]  # last user+assistant
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
        intro = (
            "This is the user's condensed Kundli data for reference during the chat:\n"
            f"{json.dumps(build_prompt_kundli_context(kundli), ensure_ascii=False)}"
        )
        # Add a system-style message into the session's memory so the chain can use it later
        # Use SystemMessage so it's distinguishable in memory
        chain.memory.chat_memory.add_user_message("My birth details")
        chain.memory.chat_memory.add_message(SystemMessage(content=intro))
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

    # append kundli if available for the session (keep a compact snippet)
    kundli = get_kundli(session_id)
    if kundli:
        prompt_kundli = build_prompt_kundli_context(kundli, user_query)
        kundli_str = json.dumps(prompt_kundli, ensure_ascii=False)
        response_style = build_response_style_instructions(user_query=user_query)
        reasoning_framework = build_astrology_reasoning_framework(user_query=user_query)
        final_input = (
            "You are a master Vedic astrologer (Jyotishi) with decades of practical experience.\n"
            "Use only the provided Kundli data. Do not invent dates, dashas, yogas, transits, remedies, or chart facts.\n\n"
            f"{reasoning_framework}\n"
            "### Non-Negotiable Rules\n"
            "1. Treat the natal chart as primary.\n"
            "2. Use D9 only as supporting evidence for marriage/spouse/dharma questions when it is provided.\n"
            "3. Use D10 only as supporting evidence for career/profession/public-role questions when it is provided.\n"
            "4. For timing questions, cite exact dasha dates from the provided data and give concrete windows only when the data supports them.\n"
            "5. Treat dasha-lord sign and house as natal placement, not house rulership. Rahu and Ketu are placements, not house lords.\n"
            "6. When aspects are relevant, explicitly name which planet aspects which house or planet and whether it is a standard or special aspect.\n"
            "7. If you mention exalted, debilitated, own-sign, moolatrikona, combust, functional benefic, or functional malefic, explain plainly what that means in this person's life.\n"
            "8. For children questions, use the 5th house, 5th lord, Jupiter, occupants, and relevant aspects. Never call the 12th house the house of children.\n"
            "9. For siblings questions, use the 3rd house for younger siblings and the 11th for elder siblings. Never call the 5th house the sibling house.\n"
            "10. If the chart is mixed, say the result is mixed. Do not pretend weak evidence is certain.\n"
            "11. Do not answer requests for death prediction, cause of death, or exact death timing. Briefly refuse and offer safer guidance such as health, longevity habits, or difficult periods instead.\n\n"
            "### Response Style\n"
            "- Sound like a skilled astrologer, not a hesitant chatbot.\n"
            "- Be specific and evidence-based: prefer 'the chart strongly shows' over vague hedging.\n"
            "- Connect every important conclusion back to house, lord, planet, aspect, yoga, dasha, or divisional-chart evidence.\n"
            "- If the user asks for detail, go deep and structured rather than becoming repetitive.\n"
            "- When the question naturally involves obstacles, delay, emotional strain, or a desire for improvement, end with 2 to 4 actionable Vedic remedies such as mantra, charity, fasting, worship, or discipline-based practices.\n"
            "- Mention gemstones only when the chart support is clear and the recommendation is not reckless.\n"
            "- Use Markdown and make the answer readable and complete. No tables.\n\n"
            f"{response_style}\n"
            f"User Query: {user_query}\n\n"
            f"Reference Kundli Data:\n{kundli_str}"
        )
    else:
        final_input = user_query
    prune_memory_keep_last(chain, keep_last_pairs=1)
    # run the conversation chain
    try:
        # Note: ConversationChain.predict may be synchronous depending on LangChain adapter
        resp_text = chain.predict(input=final_input).strip()
        resp_text = complete_if_truncated(resp_text)
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
