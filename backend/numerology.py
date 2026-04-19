from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Any, Dict, List, Tuple


MASTER_NUMBERS = {11, 22, 33}
VOWELS = set("AEIOU")

PYTHAGOREAN_VALUES = {
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "E": 5,
    "F": 6,
    "G": 7,
    "H": 8,
    "I": 9,
    "J": 1,
    "K": 2,
    "L": 3,
    "M": 4,
    "N": 5,
    "O": 6,
    "P": 7,
    "Q": 8,
    "R": 9,
    "S": 1,
    "T": 2,
    "U": 3,
    "V": 4,
    "W": 5,
    "X": 6,
    "Y": 7,
    "Z": 8,
}

NUMBER_MEANINGS = {
    1: {
        "title": "The Pioneer",
        "essence": "Independent, initiating, and driven to carve a path.",
        "keywords": ["leadership", "courage", "self-direction"],
        "gifts": ["starting new chapters", "making fast decisions", "standing on your own feet"],
        "growth": ["learning patience", "collaborating without losing autonomy", "avoiding ego battles"],
    },
    2: {
        "title": "The Harmonizer",
        "essence": "Diplomatic, intuitive, and naturally tuned to partnership.",
        "keywords": ["cooperation", "sensitivity", "balance"],
        "gifts": ["building trust", "reading emotional nuance", "creating peace"],
        "growth": ["setting boundaries", "speaking directly", "not outsourcing self-worth"],
    },
    3: {
        "title": "The Creative Voice",
        "essence": "Expressive, social, and animated by imagination.",
        "keywords": ["communication", "joy", "artistry"],
        "gifts": ["storytelling", "uplifting others", "bringing color to ideas"],
        "growth": ["following through", "staying grounded", "not scattering energy"],
    },
    4: {
        "title": "The Builder",
        "essence": "Practical, consistent, and strongest when creating structure.",
        "keywords": ["discipline", "stability", "systems"],
        "gifts": ["reliability", "craftsmanship", "turning plans into reality"],
        "growth": ["loosening rigidity", "welcoming change", "making space for spontaneity"],
    },
    5: {
        "title": "The Explorer",
        "essence": "Adaptive, freedom-loving, and energized by change.",
        "keywords": ["movement", "curiosity", "versatility"],
        "gifts": ["reinvention", "learning quickly", "thriving in dynamic settings"],
        "growth": ["building consistency", "avoiding impulsive choices", "staying present with limits"],
    },
    6: {
        "title": "The Nurturer",
        "essence": "Caring, responsible, and oriented toward service and beauty.",
        "keywords": ["care", "responsibility", "devotion"],
        "gifts": ["supporting loved ones", "creating harmony", "holding communities together"],
        "growth": ["releasing perfectionism", "not over-carrying others", "receiving help"],
    },
    7: {
        "title": "The Seeker",
        "essence": "Reflective, analytical, and drawn to wisdom beneath the surface.",
        "keywords": ["insight", "study", "depth"],
        "gifts": ["research", "discernment", "spiritual inquiry"],
        "growth": ["opening emotionally", "trusting timing", "not isolating too much"],
    },
    8: {
        "title": "The Executive",
        "essence": "Ambitious, strategic, and focused on mastery in the material world.",
        "keywords": ["power", "achievement", "management"],
        "gifts": ["leading at scale", "building wealth", "taking ownership"],
        "growth": ["balancing work with heart", "using authority ethically", "softening control"],
    },
    9: {
        "title": "The Humanitarian",
        "essence": "Compassionate, idealistic, and motivated by service beyond the self.",
        "keywords": ["service", "compassion", "completion"],
        "gifts": ["big-picture wisdom", "forgiveness", "guiding others through endings"],
        "growth": ["avoiding martyrdom", "staying practical", "letting go with clarity"],
    },
    11: {
        "title": "The Inspirer",
        "essence": "Visionary, heightened in sensitivity, and meant to illuminate others.",
        "keywords": ["intuition", "illumination", "inspiration"],
        "gifts": ["channeling ideas", "awakening others", "bridging logic and spirit"],
        "growth": ["grounding nervous intensity", "trusting your voice", "working steadily with vision"],
    },
    22: {
        "title": "The Master Builder",
        "essence": "Capable of turning a bold vision into durable real-world impact.",
        "keywords": ["mastery", "execution", "legacy"],
        "gifts": ["large-scale building", "practical vision", "organizational power"],
        "growth": ["avoiding overwhelm", "working step by step", "not shrinking from responsibility"],
    },
    33: {
        "title": "The Teacher",
        "essence": "Heart-led, compassionate, and called toward healing through service.",
        "keywords": ["teaching", "healing", "selfless service"],
        "gifts": ["mentoring", "lifting collective morale", "leading through care"],
        "growth": ["protecting energy", "not rescuing everyone", "accepting human imperfection"],
    },
}


class NumerologyInputError(ValueError):
    pass


def _normalize_name(full_name: str) -> str:
    if not isinstance(full_name, str) or not full_name.strip():
        raise NumerologyInputError("Full name is required.")

    ascii_name = (
        unicodedata.normalize("NFKD", full_name)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    cleaned = re.sub(r"[^A-Za-z\s]", " ", ascii_name).upper()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        raise NumerologyInputError("Please enter a name with alphabetic characters.")
    return cleaned


def _parse_birth_date(value: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise NumerologyInputError("Date of birth is required.")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise NumerologyInputError("Date of birth must use the YYYY-MM-DD format.") from exc


def _reduce_number(value: int, keep_master_numbers: bool = True) -> Tuple[int, List[Dict[str, Any]]]:
    current = int(value)
    steps: List[Dict[str, Any]] = []
    while current > 9 and not (keep_master_numbers and current in MASTER_NUMBERS):
        digits = [int(ch) for ch in str(current)]
        total = sum(digits)
        steps.append({"value": current, "digits": digits, "total": total})
        current = total
    return current, steps


def _render_reduction(value: int, steps: List[Dict[str, Any]]) -> str:
    if not steps:
        return str(value)
    pieces = [str(value)]
    for step in steps:
        pieces.append(str(step["total"]))
    return " -> ".join(pieces)


def _letters_with_values(text: str) -> List[Dict[str, Any]]:
    letters = []
    for char in text:
        if char in PYTHAGOREAN_VALUES:
            letters.append({"letter": char, "value": PYTHAGOREAN_VALUES[char]})
    return letters


def _sum_letters(text: str, include_vowels: bool | None = None) -> Dict[str, Any]:
    pairs = _letters_with_values(text)
    if include_vowels is True:
        pairs = [item for item in pairs if item["letter"] in VOWELS]
    elif include_vowels is False:
        pairs = [item for item in pairs if item["letter"] not in VOWELS]

    total = sum(item["value"] for item in pairs)
    reduced, steps = _reduce_number(total)
    calculation = " + ".join(str(item["value"]) for item in pairs) if pairs else "0"
    return {
        "letters": [item["letter"] for item in pairs],
        "values": [item["value"] for item in pairs],
        "total": total,
        "reduced": reduced,
        "steps": steps,
        "calculation": calculation,
    }


def _build_number_payload(
    key: str,
    label: str,
    total: int,
    reduced: int,
    steps: List[Dict[str, Any]],
    calculation: str,
) -> Dict[str, Any]:
    meaning = NUMBER_MEANINGS[reduced]
    return {
        "key": key,
        "label": label,
        "number": reduced,
        "raw_total": total,
        "title": meaning["title"],
        "essence": meaning["essence"],
        "keywords": meaning["keywords"],
        "gifts": meaning["gifts"],
        "growth": meaning["growth"],
        "calculation": calculation,
        "reduction": _render_reduction(total, steps),
    }


def build_numerology_profile(full_name: str, date_of_birth: str) -> Dict[str, Any]:
    normalized_name = _normalize_name(full_name)
    birth_date = _parse_birth_date(date_of_birth)

    date_digits = [int(ch) for ch in birth_date.strftime("%Y%m%d")]
    life_path_total = sum(date_digits)
    life_path_number, life_path_steps = _reduce_number(life_path_total)

    birthday_total = birth_date.day
    birthday_number, birthday_steps = _reduce_number(birthday_total)

    attitude_total = birth_date.month + birth_date.day
    attitude_number, attitude_steps = _reduce_number(attitude_total)

    name_total = _sum_letters(normalized_name, include_vowels=None)
    vowels_total = _sum_letters(normalized_name, include_vowels=True)
    consonants_total = _sum_letters(normalized_name, include_vowels=False)

    core_numbers = [
        _build_number_payload(
            "life_path",
            "Life Path",
            life_path_total,
            life_path_number,
            life_path_steps,
            f"{' + '.join(str(digit) for digit in date_digits)} = {life_path_total}",
        ),
        _build_number_payload(
            "destiny",
            "Destiny / Expression",
            name_total["total"],
            name_total["reduced"],
            name_total["steps"],
            f"{name_total['calculation']} = {name_total['total']}",
        ),
        _build_number_payload(
            "soul_urge",
            "Soul Urge",
            vowels_total["total"],
            vowels_total["reduced"],
            vowels_total["steps"],
            f"{vowels_total['calculation']} = {vowels_total['total']}",
        ),
        _build_number_payload(
            "personality",
            "Personality",
            consonants_total["total"],
            consonants_total["reduced"],
            consonants_total["steps"],
            f"{consonants_total['calculation']} = {consonants_total['total']}",
        ),
        _build_number_payload(
            "birthday",
            "Birthday Number",
            birthday_total,
            birthday_number,
            birthday_steps,
            str(birthday_total),
        ),
        _build_number_payload(
            "attitude",
            "Attitude",
            attitude_total,
            attitude_number,
            attitude_steps,
            f"{birth_date.month} + {birth_date.day} = {attitude_total}",
        ),
    ]

    number_lookup = {item["key"]: item for item in core_numbers}
    life_path = number_lookup["life_path"]
    destiny = number_lookup["destiny"]
    soul_urge = number_lookup["soul_urge"]
    personality = number_lookup["personality"]

    highlights = [
        f"Life Path {life_path['number']} points to a core journey around {', '.join(life_path['keywords'])}.",
        f"Destiny {destiny['number']} shows how your natural contribution tends to be expressed through {destiny['title'].lower()}.",
        f"Soul Urge {soul_urge['number']} describes what motivates you internally, while Personality {personality['number']} reflects what people tend to notice first.",
    ]

    return {
        "input": {
            "full_name": full_name.strip(),
            "normalized_name": normalized_name,
            "date_of_birth": birth_date.isoformat(),
        },
        "system": {
            "name_method": "Pythagorean numerology",
            "date_method": "Digit reduction with master numbers 11, 22, and 33 preserved",
        },
        "core_numbers": core_numbers,
        "highlights": highlights,
        "notes": [
            "This tool uses the full birth name you enter and reduces date totals while preserving master numbers 11, 22, and 33.",
            "For simplicity, vowels are counted as A, E, I, O, and U; the letter Y is treated as a consonant in this version.",
        ],
        "name_breakdown": {
            "all_letters": name_total["letters"],
            "vowels": vowels_total["letters"],
            "consonants": consonants_total["letters"],
        },
    }
