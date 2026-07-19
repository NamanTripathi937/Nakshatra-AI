import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from threading import Lock
from fastapi import HTTPException

from database import get_sessions_collection
from astro.astro import (
    DEBILITATION_SIGNS,
    EXALTATION_SIGNS,
    MOOLATRIKONA_RANGES,
    OWN_SIGNS,
    generate_chart,
)
from app.core.dependencies import serialize_datetime_value
from app.core.constants import (
    ZODIAC_SIGNS,
    SIGN_RULERS,
    SIGN_KEYWORDS,
    HOUSE_THEMES,
    PLANET_THEMES,
    PLANET_DISPLAY_ORDER,
    PLANET_SORT_ORDER,
    PLANET_SHORT_SYMBOLS,
    CHART_OPTIONS,
    CHART_EXPORT_SUMMARIES,
    ASHTAKOOT_VARNA_POINTS,
    ASHTAKOOT_VASHYA_POINTS,
    ASHTAKOOT_TARA_POINTS,
    ASHTAKOOT_YONI_POINTS,
    ASHTAKOOT_GRAHA_MAITRI_POINTS,
    ASHTAKOOT_GANA_POINTS,
    ASHTAKOOT_BHAKOOT_POINTS,
    ASHTAKOOT_NADI_POINTS,
    ASHTAKOOT_VARNA_NAMES,
    ASHTAKOOT_VASHYA_NAMES,
    ASHTAKOOT_YONI_NAMES,
    ASHTAKOOT_GRAHA_LORD_NAMES,
    ASHTAKOOT_GANA_NAMES,
    ASHTAKOOT_NADI_NAMES,
    ASHTAKOOT_EXPLANATIONS,
    NATURAL_BENEFICS,
    REMEDY_PRIORITY_PLANETS,
    GEMSTONE_MAP,
    MANTRA_MAP,
    FASTING_MAP,
    CHARITY_MAP,
    RUDRAKSHA_MAP,
)

logger = logging.getLogger("nakshatra-backend")

# ----- Per-session stores (thread-safe) -----
_kundli_store: Dict[str, Dict[str, Any]] = {}
_kundli_lock = Lock()

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


# ----- Ashtakoot scoring helpers -----

def get_ashtakoot_varna_class(moon_sign_index: int) -> int:
    if moon_sign_index in {4, 8, 12}:
        return 0
    if moon_sign_index in {1, 5, 9}:
        return 1
    if moon_sign_index in {2, 6, 10}:
        return 2
    return 3


def get_ashtakoot_vashya_group(moon_sign_index: int) -> int:
    if moon_sign_index in {3, 6, 7, 9, 11}:
        return 0
    if moon_sign_index == 5:
        return 1
    if moon_sign_index in {1, 2, 10}:
        return 2
    if moon_sign_index in {4, 12}:
        return 3
    return 4


def get_ashtakoot_tara_group(nakshatra_index: int) -> int:
    if nakshatra_index < 10:
        return nakshatra_index - 1
    if nakshatra_index <= 18:
        return int(str(nakshatra_index)[-1])
    return int(str(nakshatra_index)[-1]) + 1


def get_ashtakoot_yoni_animal(nakshatra_index: int) -> int:
    animal_mappings = {
        1: 0,
        2: 1,
        3: 2,
        4: 3,
        5: 3,
        6: 4,
        7: 5,
        8: 2,
        9: 5,
        10: 6,
        11: 6,
        12: 7,
        13: 8,
        14: 9,
        15: 8,
        16: 9,
        17: 11,
        18: 10,
        19: 4,
        20: 11,
        21: 12,
        22: 11,
        23: 13,
        24: 0,
        25: 13,
        26: 7,
        27: 1,
        28: 12,
    }
    return animal_mappings[nakshatra_index]


def get_ashtakoot_sign_lord(moon_sign_index: int) -> int:
    sign_lord_mappings = {
        5: 0,
        4: 1,
        1: 2,
        8: 2,
        3: 3,
        6: 3,
        9: 4,
        12: 4,
        2: 5,
        7: 5,
        10: 6,
        11: 6,
    }
    return sign_lord_mappings[moon_sign_index]


def get_ashtakoot_gana(nakshatra_index: int) -> int:
    if nakshatra_index in {1, 5, 7, 8, 13, 15, 17, 22, 27}:
        return 0
    if nakshatra_index in {2, 4, 6, 11, 12, 20, 21, 25, 26}:
        return 1
    return 2


def get_ashtakoot_nadi(nakshatra_index: int) -> int:
    if nakshatra_index in {1, 6, 7, 12, 13, 18, 19, 24, 25}:
        return 0
    if nakshatra_index in {2, 5, 8, 11, 14, 17, 20, 23, 26}:
        return 1
    return 2


def extract_moon_match_profile(kundli: Dict[str, Any], name: Optional[str] = None) -> Dict[str, Any]:
    moon = next(
        (
            planet for planet in kundli.get("planets", [])
            if planet.get("name") == "Moon" and "error" not in planet
        ),
        None,
    )
    janma = kundli.get("janma_nakshatra") or {}
    if not moon or not janma.get("index"):
        raise HTTPException(status_code=500, detail="Moon or Janma Nakshatra data missing for compatibility check")

    moon_sign_index = int(moon.get("sign_index"))
    nakshatra_index = int(janma.get("index"))
    return {
        "name": name or "Native",
        "moon_sign_index": moon_sign_index,
        "moon_sign": moon.get("sign"),
        "nakshatra_index": nakshatra_index,
        "nakshatra_name": janma.get("name"),
        "nakshatra_pada": janma.get("pada"),
    }


def normalize_match_role(value: Optional[str]) -> str:
    role = str(value or "").strip().lower()
    if role not in {"bride", "groom"}:
        raise HTTPException(status_code=400, detail="native_role must be either 'bride' or 'groom'")
    return role


def build_ashtakoot_breakdown(bride: Dict[str, Any], groom: Dict[str, Any]) -> List[Dict[str, Any]]:
    bride_varna = get_ashtakoot_varna_class(bride["moon_sign_index"])
    groom_varna = get_ashtakoot_varna_class(groom["moon_sign_index"])
    bride_vashya = get_ashtakoot_vashya_group(bride["moon_sign_index"])
    groom_vashya = get_ashtakoot_vashya_group(groom["moon_sign_index"])
    bride_tara = get_ashtakoot_tara_group(bride["nakshatra_index"])
    groom_tara = get_ashtakoot_tara_group(groom["nakshatra_index"])
    bride_yoni = get_ashtakoot_yoni_animal(bride["nakshatra_index"])
    groom_yoni = get_ashtakoot_yoni_animal(groom["nakshatra_index"])
    bride_lord = get_ashtakoot_sign_lord(bride["moon_sign_index"])
    groom_lord = get_ashtakoot_sign_lord(groom["moon_sign_index"])
    bride_gana = get_ashtakoot_gana(bride["nakshatra_index"])
    groom_gana = get_ashtakoot_gana(groom["nakshatra_index"])
    bride_nadi = get_ashtakoot_nadi(bride["nakshatra_index"])
    groom_nadi = get_ashtakoot_nadi(groom["nakshatra_index"])

    raw_items = [
        {
            "key": "varna",
            "score": float(ASHTAKOOT_VARNA_POINTS[bride_varna][groom_varna]),
            "out_of": float(ASHTAKOOT_EXPLANATIONS["varna"]["out_of"]),
            "bride_value": ASHTAKOOT_VARNA_NAMES[bride_varna],
            "groom_value": ASHTAKOOT_VARNA_NAMES[groom_varna],
        },
        {
            "key": "vashya",
            "score": float(ASHTAKOOT_VASHYA_POINTS[bride_vashya][groom_vashya]),
            "out_of": float(ASHTAKOOT_EXPLANATIONS["vashya"]["out_of"]),
            "bride_value": ASHTAKOOT_VASHYA_NAMES[bride_vashya],
            "groom_value": ASHTAKOOT_VASHYA_NAMES[groom_vashya],
        },
        {
            "key": "tara",
            "score": float(ASHTAKOOT_TARA_POINTS[bride_tara][groom_tara]),
            "out_of": float(ASHTAKOOT_EXPLANATIONS["tara"]["out_of"]),
            "bride_value": bride["nakshatra_name"],
            "groom_value": groom["nakshatra_name"],
        },
        {
            "key": "yoni",
            "score": float(ASHTAKOOT_YONI_POINTS[bride_yoni][groom_yoni]),
            "out_of": float(ASHTAKOOT_EXPLANATIONS["yoni"]["out_of"]),
            "bride_value": ASHTAKOOT_YONI_NAMES[bride_yoni],
            "groom_value": ASHTAKOOT_YONI_NAMES[groom_yoni],
        },
        {
            "key": "graha_maitri",
            "score": float(ASHTAKOOT_GRAHA_MAITRI_POINTS[bride_lord][groom_lord]),
            "out_of": float(ASHTAKOOT_EXPLANATIONS["graha_maitri"]["out_of"]),
            "bride_value": ASHTAKOOT_GRAHA_LORD_NAMES[bride_lord],
            "groom_value": ASHTAKOOT_GRAHA_LORD_NAMES[groom_lord],
        },
        {
            "key": "gana",
            "score": float(ASHTAKOOT_GANA_POINTS[bride_gana][groom_gana]),
            "out_of": float(ASHTAKOOT_EXPLANATIONS["gana"]["out_of"]),
            "bride_value": ASHTAKOOT_GANA_NAMES[bride_gana],
            "groom_value": ASHTAKOOT_GANA_NAMES[groom_gana],
        },
        {
            "key": "bhakoot",
            "score": float(ASHTAKOOT_BHAKOOT_POINTS[bride["moon_sign_index"] - 1][groom["moon_sign_index"] - 1]),
            "out_of": float(ASHTAKOOT_EXPLANATIONS["bhakoot"]["out_of"]),
            "bride_value": bride["moon_sign"],
            "groom_value": groom["moon_sign"],
        },
        {
            "key": "nadi",
            "score": float(ASHTAKOOT_NADI_POINTS[bride_nadi][groom_nadi]),
            "out_of": float(ASHTAKOOT_EXPLANATIONS["nadi"]["out_of"]),
            "bride_value": ASHTAKOOT_NADI_NAMES[bride_nadi],
            "groom_value": ASHTAKOOT_NADI_NAMES[groom_nadi],
        },
    ]

    breakdown: List[Dict[str, Any]] = []
    for item in raw_items:
        meta = ASHTAKOOT_EXPLANATIONS[item["key"]]
        ratio = (item["score"] / item["out_of"]) if item["out_of"] else 0.0
        if ratio >= 0.75:
            interpretation = meta["strength"]
        elif ratio <= 0.34:
            interpretation = meta["challenge"]
        else:
            interpretation = f"This area is moderate: {meta['meaning']} show some support, but it is not completely effortless."

        breakdown.append(
            {
                "key": item["key"],
                "title": meta["title"],
                "score": item["score"],
                "out_of": item["out_of"],
                "meaning": meta["meaning"],
                "bride_value": item["bride_value"],
                "groom_value": item["groom_value"],
                "interpretation": interpretation,
                "ratio": ratio,
            }
        )

    return breakdown


def classify_guna_match(total_score: float) -> Dict[str, str]:
    if total_score >= 30:
        return {
            "label": "Excellent Match",
            "summary": "This is an excellent Ashtakoot score and traditionally shows strong marriage potential.",
        }
    if total_score >= 24:
        return {
            "label": "Very Good Match",
            "summary": "This is a very good compatibility score with solid support for marriage and long-term adjustment.",
        }
    if total_score >= 18:
        return {
            "label": "Good to Moderate Match",
            "summary": "This clears the traditional minimum comfort zone, but a few areas will need maturity and conscious handling.",
        }
    return {
        "label": "Challenging Match",
        "summary": "This is below the traditional comfort threshold, so marriage would need extra care, compatibility awareness, and family guidance.",
    }


def build_compatibility_insights(breakdown: List[Dict[str, Any]]) -> Dict[str, Any]:
    ordered = sorted(breakdown, key=lambda item: (item["ratio"], item["out_of"]))
    challenges = [item for item in ordered if item["ratio"] <= 0.5][:3]
    strengths = [item for item in sorted(breakdown, key=lambda item: (-item["ratio"], -item["out_of"])) if item["ratio"] >= 0.75][:3]

    if strengths:
        best = strengths[0]
        best_part = f"The best part of this marriage is likely to be {best['meaning']}, because {best['title']} is one of the strongest areas in the match."
    else:
        best = max(breakdown, key=lambda item: item["ratio"])
        best_part = f"The best part of this marriage is likely to come from {best['meaning']}, which is comparatively stronger than the rest of the match."

    challenge_lines = [
        f"{item['title']}: {item['interpretation']}"
        for item in challenges
    ]
    strength_lines = [
        f"{item['title']}: {item['interpretation']}"
        for item in strengths
    ]

    return {
        "strengths": strength_lines,
        "challenges": challenge_lines,
        "best_part_about_marriage": best_part,
    }


def build_ashtakoot_match_response(
    native_kundli: Dict[str, Any],
    partner_kundli: Dict[str, Any],
    native_name: Optional[str],
    partner_name: Optional[str],
    native_role: str,
) -> Dict[str, Any]:
    native_profile = extract_moon_match_profile(native_kundli, native_name or "You")
    partner_profile = extract_moon_match_profile(partner_kundli, partner_name or "Partner")

    if native_role == "bride":
        bride = native_profile
        groom = partner_profile
    else:
        bride = partner_profile
        groom = native_profile

    breakdown = build_ashtakoot_breakdown(bride, groom)
    total_score = round(sum(item["score"] for item in breakdown), 1)
    verdict = classify_guna_match(total_score)
    insights = build_compatibility_insights(breakdown)

    return {
        "native_name": native_profile["name"],
        "partner_name": partner_profile["name"],
        "native_role": native_role,
        "partner_role": "groom" if native_role == "bride" else "bride",
        "total_score": total_score,
        "out_of": 36,
        "verdict": verdict["label"],
        "score_summary": f"{total_score}/36 gunas match.",
        "compatibility_summary": verdict["summary"],
        "breakdown": breakdown,
        "strengths": insights["strengths"],
        "challenges": insights["challenges"],
        "best_part_about_marriage": insights["best_part_about_marriage"],
        "traditional_note": "Traditionally, 18 or more gunas is considered workable, 24+ is strong, and 30+ is excellent.",
    }


# ----- Kundli analysis details -----

def find_next_mahadasha(kundli: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    timeline = kundli.get("vimshottari_dasha", {}).get("mahadashas", [])
    for idx, maha in enumerate(timeline):
        if maha.get("is_current"):
            if idx + 1 < len(timeline):
                return timeline[idx + 1]
            return None
    return None


def summarize_planets(kundli: Dict[str, Any], names: List[str]) -> List[Dict[str, Any]]:
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


def summarize_vedic_aspects(kundli: Dict[str, Any], names: List[str]) -> Dict[str, Any]:
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
    names: List[str],
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
    key_planets: List[str],
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


def build_condition_tags(planet_name: str, kundli: Dict[str, Any], planet: Dict[str, Any]) -> List[str]:
    conditions = (kundli.get("planetary_conditions") or {}).get(planet_name) or planet.get("conditions") or {}
    tags: List[str] = []

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


def summarize_house_lord_lines(kundli: Dict[str, Any], planet_lookup: Dict[str, Dict[str, Any]]) -> List[str]:
    house_lords = (kundli.get("yoga_analysis") or {}).get("house_lords") or {}
    entries: List[str] = []
    for house_no in range(1, 13):
        house_info = house_lords.get(str(house_no), {})
        lord_name = canonical_planet_name(house_info.get("lord"))
        lord = planet_lookup.get(lord_name)
        if lord:
            entries.append(f"{house_no}L {lord_name}->{lord.get('sign')} {lord.get('house')}H")
        elif lord_name:
            entries.append(f"{house_no}L {lord_name}")

    lines: List[str] = []
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

    upcoming_parts: List[str] = []
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


def summarize_current_dasha(kundli: Dict[str, Any]) -> str:
    current_line, _ = summarize_dasha_timeline(kundli)
    return current_line


def summarize_divisional_notes(kundli: Dict[str, Any]) -> List[str]:
    notes: List[str] = []
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


def summarize_aspect_notes(kundli: Dict[str, Any]) -> List[str]:
    aspect_data = (kundli.get("vedic_aspects") or {}).get("by_planet") or {}
    lines: List[str] = []

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


def summarize_gochar_notes(kundli: Dict[str, Any]) -> List[str]:
    gochar = kundli.get("gochar") or {}
    focus = gochar.get("focus") or {}
    evaluated_at = gochar.get("evaluated_at")
    lines: List[str] = []

    if evaluated_at:
        lines.append(f"- Evaluated at: {evaluated_at}.")

    for name in ["Moon", "Jupiter", "Saturn", "Rahu", "Ketu"]:
        planet = focus.get(name)
        if not planet:
            continue
        line = (
            f"- {name}: {planet.get('sign')} "
            f"{planet.get('house_from_lagna')}H from Lagna"
        )
        if planet.get("house_from_natal_moon") is not None:
            line += f", {planet.get('house_from_natal_moon')}H from natal Moon"
        if planet.get("retrograde"):
            line += ", retrograde"
        line += "."
        lines.append(line)

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

    gochar_notes = summarize_gochar_notes(kundli)
    if gochar_notes:
        lines.append("Current gochar:")
        lines.extend(gochar_notes)

    divisional_notes = summarize_divisional_notes(kundli)
    if divisional_notes:
        lines.append("Divisional notes:")
        lines.extend(divisional_notes)

    aspect_notes = summarize_aspect_notes(kundli)
    if aspect_notes:
        lines.append("Aspect highlights:")
        lines.extend(aspect_notes)

    remedy_notes = summarize_rule_based_remedies(kundli)
    if remedy_notes:
        lines.append("Rule-based remedies:")
        lines.extend(remedy_notes)

    return "\n".join(lines)


def build_free_tier_chart_summary(kundli: Dict[str, Any], profile: Optional[Dict[str, Any]] = None) -> str:
    profile = profile or {}
    planet_lookup = build_planet_lookup(kundli)
    asc = kundli.get("ascendant") or {}
    janma = kundli.get("janma_nakshatra") or {}
    current_line, upcoming_line = summarize_dasha_timeline(kundli)
    lines = [
        "FREE TIER CHART SUMMARY:",
        f"Name: {profile.get('full_name') or 'Native'}",
        f"Lagna: {asc.get('sign', 'Unknown')} ({SIGN_KEYWORDS.get(asc.get('sign'), 'general temperament')})",
    ]
    if janma.get("name"):
        lines.append(f"Janma Nakshatra: {janma.get('name')} pada {janma.get('pada', '?')}")
    lines.append("Natal placements:")
    for planet_name in PLANET_DISPLAY_ORDER:
        planet = planet_lookup.get(planet_name)
        if planet:
            lines.append(summarize_planet_line(planet_name, kundli, planet))
    house_lord_lines = summarize_house_lord_lines(kundli, planet_lookup)
    if house_lord_lines:
        lines.append("House lord map:")
        lines.extend(house_lord_lines)
    lines.append(f"Key yogas: {summarize_yogas(kundli)}")
    lines.append(f"Current dasha: {current_line}")
    lines.append(f"Upcoming periods: {upcoming_line}")
    gochar_notes = summarize_gochar_notes(kundli)
    if gochar_notes:
        lines.append("Current gochar:")
        lines.extend(gochar_notes)
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
    statuses: List[str],
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
    statuses: List[str],
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


def join_phrases(parts: List[str]) -> str:
    filtered = [part for part in parts if part]
    if not filtered:
        return ""
    if len(filtered) == 1:
        return filtered[0]
    if len(filtered) == 2:
        return f"{filtered[0]} and {filtered[1]}"
    return ", ".join(filtered[:-1]) + f", and {filtered[-1]}"


def build_planet_remedy_profile(
    kundli: Dict[str, Any],
    lagna_lord: Optional[str],
    detail: Dict[str, Any],
) -> Dict[str, Any]:
    planet_name = detail["name"]
    house = int(detail.get("house") or 0)
    statuses = detail.get("statuses") or []
    condition_data = get_chart_condition_data(kundli, planet_name)
    functional_status = (condition_data.get("functional_nature") or {}).get("status")

    support_score = 0
    support_reasons: List[str] = []
    weakness_score = 0
    weakness_reasons: List[str] = []

    if planet_name == lagna_lord:
        support_score += 3
        support_reasons.append("it is the Lagna lord")
    if functional_status == "functional_benefic":
        support_score += 2
        support_reasons.append("it acts as a functional benefic for this ascendant")
    elif functional_status == "mixed":
        support_score += 1
        support_reasons.append("it gives mixed but usable results in this chart")
    elif functional_status == "functional_malefic":
        support_score -= 2
        weakness_score += 1
        weakness_reasons.append("it behaves as a functional malefic for this ascendant")

    if planet_name in NATURAL_BENEFICS and functional_status != "functional_malefic":
        support_score += 1
        support_reasons.append("it is naturally benefic")

    if "Debilitated" in statuses:
        weakness_score += 3
        weakness_reasons.append("it is debilitated")
    if "Combust" in statuses:
        weakness_score += 2
        weakness_reasons.append("it is combust")
    if house in {6, 8, 12}:
        weakness_score += 1
        weakness_reasons.append(f"it sits in the {house}th house")

    if "Exalted" in statuses:
        weakness_score -= 2
        support_reasons.append("it is exalted")
    if "Own Sign" in statuses:
        weakness_score -= 2
        support_reasons.append("it is in its own sign")
    if "Moolatrikona" in statuses:
        weakness_score -= 1
        support_reasons.append("it is in moolatrikona")
    if "Vargottama" in statuses:
        weakness_score -= 1
        support_reasons.append("it is vargottama")

    weakness_score = max(0, weakness_score)
    affliction_score = weakness_score
    if functional_status == "functional_malefic":
        affliction_score += 1

    return {
        "planet": planet_name,
        "house": house,
        "sign": detail.get("sign"),
        "statuses": statuses,
        "support_score": support_score,
        "support_reasons": support_reasons,
        "weakness_score": weakness_score,
        "weakness_reasons": weakness_reasons,
        "affliction_score": affliction_score,
        "functional_status": functional_status,
    }


def build_supportive_reason(profile: Dict[str, Any]) -> str:
    support_text = join_phrases(profile.get("support_reasons") or [])
    weakness_text = join_phrases(profile.get("weakness_reasons") or [])
    if support_text and weakness_text:
        return f"{profile['planet']} is supportive here because {support_text}, but it still needs help because {weakness_text}."
    if support_text:
        return f"{profile['planet']} is supportive here because {support_text}."
    if weakness_text:
        return f"{profile['planet']} needs strengthening because {weakness_text}."
    return f"{profile['planet']} can be supported gently through traditional remedial measures."


def build_affliction_reason(profile: Dict[str, Any]) -> str:
    weakness_text = join_phrases(profile.get("weakness_reasons") or [])
    if weakness_text:
        return f"{profile['planet']} shows stress because {weakness_text}."
    return f"{profile['planet']} shows enough strain in the natal chart to justify a gentle remedy."


def build_rule_based_remedies(kundli: Dict[str, Any]) -> Dict[str, Any]:
    asc_sign = (kundli.get("ascendant") or {}).get("sign")
    lagna_lord = SIGN_RULERS.get(asc_sign)
    detail_map = {
        detail["name"]: detail
        for detail in build_chart_planet_details(kundli, "D1")
    }
    profiles = [
        build_planet_remedy_profile(kundli, lagna_lord, detail_map[name])
        for name in REMEDY_PRIORITY_PLANETS
        if name in detail_map
    ]

    gemstone_candidates = sorted(
        [
            profile for profile in profiles
            if profile["planet"] in GEMSTONE_MAP
            and profile["support_score"] >= 2
            and profile["weakness_score"] >= 2
            and profile["functional_status"] != "functional_malefic"
        ],
        key=lambda profile: (-profile["weakness_score"], -profile["support_score"], PLANET_SORT_ORDER.get(profile["planet"], 999)),
    )[:3]

    affliction_candidates = sorted(
        [profile for profile in profiles if profile["affliction_score"] >= 2],
        key=lambda profile: (-profile["affliction_score"], PLANET_SORT_ORDER.get(profile["planet"], 999)),
    )

    gemstones = [
        {
            "planet": profile["planet"],
            "gemstone": GEMSTONE_MAP[profile["planet"]]["name"],
            "recommendation": GEMSTONE_MAP[profile["planet"]]["recommendation"],
            "why": build_supportive_reason(profile),
            "caution": "Gemstones strengthen planets strongly, so confirm before wearing them regularly.",
        }
        for profile in gemstone_candidates
    ]

    mantras = [
        {
            "planet": profile["planet"],
            "mantra": MANTRA_MAP[profile["planet"]]["mantra"],
            "practice": MANTRA_MAP[profile["planet"]]["practice"],
            "why": build_affliction_reason(profile),
        }
        for profile in affliction_candidates[:5]
        if profile["planet"] in MANTRA_MAP
    ]

    fasting = [
        {
            "planet": profile["planet"],
            "day": FASTING_MAP[profile["planet"]]["day"],
            "practice": FASTING_MAP[profile["planet"]]["practice"],
            "why": build_affliction_reason(profile),
        }
        for profile in affliction_candidates[:4]
        if profile["planet"] in FASTING_MAP
    ]

    charity = [
        {
            "planet": profile["planet"],
            "recommendation": CHARITY_MAP[profile["planet"]]["recommendation"],
            "why": build_affliction_reason(profile),
        }
        for profile in affliction_candidates[:5]
        if profile["planet"] in CHARITY_MAP
    ]

    rudraksha = [
        {
            "planet": profile["planet"],
            "rudraksha": RUDRAKSHA_MAP[profile["planet"]]["name"],
            "recommendation": RUDRAKSHA_MAP[profile["planet"]]["recommendation"],
            "why": build_affliction_reason(profile),
        }
        for profile in affliction_candidates[:4]
        if profile["planet"] in RUDRAKSHA_MAP
    ]

    return {
        "overview": (
            "These rule-based remedies are derived from the natal chart by identifying supportive planets that need strengthening "
            "and afflicted planets that benefit from soothing, discipline, and spiritual correction."
        ),
        "gemstones": gemstones,
        "mantras": mantras,
        "fasting": fasting,
        "charity": charity,
        "rudraksha": rudraksha,
        "notes": [
            "Gemstones are best reserved for planets that are helpful for the chart but weak in expression.",
            "Mantra, charity, fasting, and rudraksha are gentler remedies than gemstones and are usually safer starting points.",
        ],
    }


def summarize_rule_based_remedies(kundli: Dict[str, Any]) -> List[str]:
    remedies = build_rule_based_remedies(kundli)
    lines: List[str] = []

    if remedies["gemstones"]:
        lines.append(
            "- Gemstones: "
            + "; ".join(f"{item['gemstone']} for {item['planet']}" for item in remedies["gemstones"][:2])
            + "."
        )
    if remedies["mantras"]:
        lines.append(
            "- Mantras: "
            + "; ".join(f"{item['planet']} mantra" for item in remedies["mantras"][:3])
            + "."
        )
    if remedies["fasting"]:
        lines.append(
            "- Fasting: "
            + "; ".join(f"{item['day']} for {item['planet']}" for item in remedies["fasting"][:3])
            + "."
        )
    if remedies["charity"]:
        lines.append(
            "- Charity: "
            + "; ".join(f"{item['planet']}-linked donation/service" for item in remedies["charity"][:3])
            + "."
        )
    if remedies["rudraksha"]:
        lines.append(
            "- Rudraksha: "
            + "; ".join(f"{item['rudraksha']} for {item['planet']}" for item in remedies["rudraksha"][:2])
            + "."
        )

    return lines


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


def build_chart_planet_details(kundli: Dict[str, Any], chart_code: str) -> List[Dict[str, Any]]:
    chart_data = get_chart_data_for_code(kundli, chart_code)
    chart_lookup = build_chart_planet_lookup(chart_data)
    natal_lookup = build_chart_planet_lookup(kundli)
    d9_lookup = build_chart_planet_lookup((kundli.get("divisional_charts") or {}).get("D9") or {})
    details: List[Dict[str, Any]] = []

    for planet_name in PLANET_DISPLAY_ORDER:
        planet = chart_lookup.get(planet_name)
        if not planet:
            continue

        statuses: List[str] = []
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


def build_chart_export_payload(
    kundli: Dict[str, Any],
    chart_code: str,
    style: str,
    details: List[Dict[str, Any]],
) -> Dict[str, Any]:
    chart_data = get_chart_data_for_code(kundli, chart_code)
    export_chart = {
        "chart": chart_code,
        "label": CHART_OPTIONS[chart_code]["label"],
        "source": CHART_OPTIONS[chart_code]["source"],
        "style": style,
        "ascendant": chart_data.get("ascendant") or {},
        "house_cusps_deg": chart_data.get("house_cusps_deg") or {},
        "planets": chart_data.get("planets") or [],
    }

    if chart_code != "D1":
        export_chart["name"] = chart_data.get("name")
        export_chart["division"] = chart_data.get("division")
        export_chart["purpose"] = chart_data.get("purpose")
        export_chart["house_system"] = chart_data.get("house_system")
        export_chart["house_lords"] = chart_data.get("house_lords") or {}
    else:
        export_chart["house_system"] = "Whole Sign"
        export_chart["janma_nakshatra"] = kundli.get("janma_nakshatra") or {}

    return {
        "chart_code": chart_code,
        "chart_label": CHART_OPTIONS[chart_code]["label"],
        "summary": CHART_EXPORT_SUMMARIES.get(chart_code, "Structured chart export."),
        "ascendant": export_chart["ascendant"],
        "details": details,
        "chart": export_chart,
    }


def get_chart_codes_for_plan(plan_access: Dict[str, Any]) -> List[str]:
    if plan_access["features"]["divisional_charts"]:
        return list(CHART_OPTIONS.keys())
    return ["D1"]


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
        "key_planets": summarize_planets(
            kundli,
            ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "TrueNode"],
        ),
    }

    from app.services.llm_service import infer_question_focus
    context["question_focus"] = infer_question_focus(user_query)

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

    from app.services.llm_service import get_first_name

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
