from typing import Dict, List, Set, Any
from jyotichart import (
    JUPITER,
    KETU,
    MARS,
    MERCURY,
    MOON,
    RAHU,
    SATURN,
    SUN,
    VENUS,
)

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
    "D60": {"label": "Shashtiamsha", "source": "divisional"},
}

CHART_EXPORT_SUMMARIES = {
    "D1": "The Lagna chart captures the natal foundation: temperament, life direction, and the main planetary framework.",
    "D9": "The Navamsha deepens the chart by showing dharma, marriage themes, and how planets mature over time.",
    "D10": "The Dashamsha focuses on vocation, visible karma, and how professional life tends to unfold.",
    "D60": "The Shashtiamsha chart reveals past-life karma, deep-seated karmic influences, and subtle strengths or weaknesses.",
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

ASHTAKOOT_VARNA_POINTS = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [1, 1, 1, 0],
    [1, 1, 1, 1],
]

ASHTAKOOT_VASHYA_POINTS = [
    [2, 0.5, 1, 0, 2],
    [0.5, 2, 0, 0, 0],
    [1, 0, 2, 2, 2],
    [0, 0, 2, 2, 0],
    [1, 0, 1, 0, 2],
]

ASHTAKOOT_TARA_POINTS = [
    [3, 3, 1.5, 3, 1.5, 3, 1.5, 3, 3],
    [3, 3, 1.5, 3, 1.5, 3, 1.5, 3, 3],
    [1.5, 1.5, 0, 1.5, 0, 1.5, 0, 1.5, 1.5],
    [3, 3, 1.5, 3, 1.5, 3, 1.5, 3, 3],
    [1.5, 1.5, 0, 1.5, 0, 1.5, 0, 1.5, 1.5],
    [3, 3, 1.5, 3, 1.5, 3, 1.5, 3, 3],
    [1.5, 1.5, 0, 1.5, 0, 1.5, 0, 1, 1],
    [3, 3, 1.5, 3, 1.5, 3, 1.5, 3, 3],
    [3, 3, 1.5, 3, 1.5, 3, 1.5, 3, 3],
]

ASHTAKOOT_YONI_POINTS = [
    [4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 1, 3, 2, 1],
    [2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],
    [2, 3, 4, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],
    [3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],
    [2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],
    [2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1],
    [2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],
    [1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1],
    [0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 2],
    [1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1],
    [1, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1],
    [3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2],
    [2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],
    [1, 0, 1, 2, 1, 1, 2, 1, 2, 1, 1, 2, 2, 4],
]

ASHTAKOOT_GRAHA_MAITRI_POINTS = [
    [5, 5, 5, 4, 5, 0, 0],
    [5, 5, 4, 1, 4, 0.5, 0.5],
    [5, 4, 5, 0.5, 5, 3, 3],
    [4, 1, 0.5, 5, 0.5, 5, 4],
    [5, 4, 5, 0.5, 5, 0.5, 3],
    [0, 0.5, 3, 5, 0.5, 5, 5],
    [0, 0.5, 3, 4, 3, 5, 5],
]

ASHTAKOOT_GANA_POINTS = [
    [6, 3, 1],
    [5, 6, 3],
    [0, 0, 6],
]

ASHTAKOOT_BHAKOOT_POINTS = [
    [7, 0, 7, 7, 0, 0, 7, 0, 0, 7, 7, 0],
    [0, 7, 0, 7, 7, 0, 0, 7, 0, 0, 7, 7],
    [7, 0, 7, 0, 7, 7, 0, 0, 7, 0, 0, 7],
    [7, 7, 0, 7, 0, 7, 7, 0, 0, 7, 0, 0],
    [0, 7, 7, 0, 7, 0, 7, 7, 0, 0, 7, 0],
    [0, 0, 7, 7, 0, 7, 0, 7, 7, 0, 0, 7],
    [7, 0, 0, 7, 7, 0, 7, 0, 7, 7, 0, 0],
    [0, 7, 0, 0, 7, 7, 0, 7, 0, 7, 7, 0],
    [0, 0, 7, 0, 0, 7, 7, 0, 7, 0, 7, 7],
    [7, 0, 0, 7, 0, 0, 7, 7, 0, 7, 0, 7],
    [7, 7, 0, 7, 7, 0, 0, 7, 7, 0, 7, 0],
    [0, 7, 7, 0, 0, 7, 0, 0, 7, 7, 0, 7],
]

ASHTAKOOT_NADI_POINTS = [
    [0, 8, 8],
    [8, 0, 8],
    [8, 8, 0],
]

ASHTAKOOT_VARNA_NAMES = ["Brahmin", "Kshatriya", "Vaishya", "Shudra"]
ASHTAKOOT_VASHYA_NAMES = ["Manava", "Vanachara", "Chatushpada", "Jalachara", "Keeta"]
ASHTAKOOT_YONI_NAMES = ["Horse", "Elephant", "Sheep", "Serpent", "Dog", "Cat", "Rat", "Cow", "Buffalo", "Tiger", "Hare", "Monkey", "Lion", "Mongoose"]
ASHTAKOOT_GRAHA_LORD_NAMES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
ASHTAKOOT_GANA_NAMES = ["Deva", "Manushya", "Rakshasa"]
ASHTAKOOT_NADI_NAMES = ["Adi", "Madhya", "Antya"]

ASHTAKOOT_EXPLANATIONS = {
    "varna": {
        "title": "Varna",
        "out_of": 1,
        "meaning": "spiritual values, ego style, and broad life philosophy",
        "strength": "The value system and broad outlook can support mutual respect in marriage.",
        "challenge": "Differences in value systems or ego style may create subtle friction in expectations.",
    },
    "vashya": {
        "title": "Vashya",
        "out_of": 2,
        "meaning": "mutual attraction, influence, and power balance",
        "strength": "The attraction pattern and influence dynamic look naturally cooperative.",
        "challenge": "Control issues or unequal influence may create power struggles over time.",
    },
    "tara": {
        "title": "Tara",
        "out_of": 3,
        "meaning": "fortune, support, and day-to-day harmony",
        "strength": "The match supports stability, luck, and day-to-day flow as a couple.",
        "challenge": "The relationship may feel uneven in timing, luck, or emotional support during key phases.",
    },
    "yoni": {
        "title": "Yoni",
        "out_of": 4,
        "meaning": "physical chemistry, intimacy, and instinctive comfort",
        "strength": "The physical and intimate chemistry looks naturally supportive.",
        "challenge": "Intimacy styles or physical comfort may require patience and conscious understanding.",
    },
    "graha_maitri": {
        "title": "Graha Maitri",
        "out_of": 5,
        "meaning": "mental compatibility, friendship, and emotional understanding",
        "strength": "The charts show scope for friendship, mental rapport, and emotional understanding.",
        "challenge": "Misunderstandings, communication gaps, or different mental styles could become a recurring issue.",
    },
    "gana": {
        "title": "Gana",
        "out_of": 6,
        "meaning": "temperament, behavior, and instinctive reactions",
        "strength": "Temperamentally, the pair can understand each other's nature and habits well.",
        "challenge": "Temperament clashes may show up in habits, reactions, and emotional style.",
    },
    "bhakoot": {
        "title": "Bhakoot",
        "out_of": 7,
        "meaning": "emotional compatibility, family direction, and shared life momentum",
        "strength": "The emotional direction of the marriage and long-term life path look aligned.",
        "challenge": "Differences in family priorities, emotional rhythm, or long-term direction may need careful handling.",
    },
    "nadi": {
        "title": "Nadi",
        "out_of": 8,
        "meaning": "health, vitality, and deeper constitutional harmony",
        "strength": "The deeper energetic rhythm of the match looks supportive for married life.",
        "challenge": "This is a traditionally sensitive area and can point to health, vitality, or deeper adjustment concerns if ignored.",
    },
}

NATURAL_BENEFICS = {"Moon", "Mercury", "Jupiter", "Venus"}
REMEDY_PRIORITY_PLANETS = ["Moon", "Mercury", "Jupiter", "Venus", "Sun", "Mars", "Saturn", "Rahu", "Ketu"]

GEMSTONE_MAP = {
    "Sun": {"name": "Ruby", "recommendation": "Wear in gold or copper on a Sunday after proper purification."},
    "Moon": {"name": "Pearl", "recommendation": "Wear in silver on a Monday after sunrise and prayer."},
    "Mars": {"name": "Red Coral", "recommendation": "Wear in copper or gold on a Tuesday with disciplined intention."},
    "Mercury": {"name": "Emerald", "recommendation": "Wear in gold or silver on a Wednesday for clarity and skill."},
    "Jupiter": {"name": "Yellow Sapphire", "recommendation": "Wear in gold on a Thursday for wisdom, support, and grace."},
    "Venus": {"name": "Diamond or White Sapphire", "recommendation": "Wear in silver or platinum on a Friday for harmony and refinement."},
    "Saturn": {"name": "Blue Sapphire", "recommendation": "Wear only with strong caution and expert confirmation before use."},
}

MANTRA_MAP = {
    "Sun": {"mantra": "Om Hraam Hreem Hraum Sah Suryaya Namah", "practice": "108 repetitions on Sundays or daily at sunrise."},
    "Moon": {"mantra": "Om Som Somaya Namah", "practice": "108 repetitions on Mondays, ideally in the evening or near moonrise."},
    "Mars": {"mantra": "Om Kraam Kreem Kraum Sah Bhaumaya Namah", "practice": "108 repetitions on Tuesdays with steadiness and restraint."},
    "Mercury": {"mantra": "Om Bum Budhaya Namah", "practice": "108 repetitions on Wednesdays for mental clarity and speech balance."},
    "Jupiter": {"mantra": "Om Graam Greem Graum Sah Gurave Namah", "practice": "108 repetitions on Thursdays with gratitude to teachers and guides."},
    "Venus": {"mantra": "Om Draam Dreem Draum Sah Shukraya Namah", "practice": "108 repetitions on Fridays for harmony, relationships, and comfort."},
    "Saturn": {"mantra": "Om Praam Preem Praum Sah Shanaye Namah", "practice": "108 repetitions on Saturdays with patience and humility."},
    "Rahu": {"mantra": "Om Raam Rahave Namah", "practice": "108 repetitions on Saturdays or during Rahu-focused sadhana for grounding."},
    "Ketu": {"mantra": "Om Kem Ketave Namah", "practice": "108 repetitions on Tuesdays or Thursdays for detachment and inner clarity."},
}

FASTING_MAP = {
    "Sun": {"day": "Sunday", "practice": "Keep a light fast or one simple sattvic meal while honoring Surya and self-discipline."},
    "Moon": {"day": "Monday", "practice": "Observe a gentle fast with calming foods, prayer, and emotional steadiness."},
    "Mars": {"day": "Tuesday", "practice": "Take one simple meal and avoid anger, haste, and unnecessary conflict."},
    "Mercury": {"day": "Wednesday", "practice": "Keep food light and use the day for mindful speech, study, and mental cleanliness."},
    "Jupiter": {"day": "Thursday", "practice": "Take a simple sattvic fast with prayer, study, and respect toward teachers and elders."},
    "Venus": {"day": "Friday", "practice": "Keep the day clean, balanced, and restrained while honoring beauty without excess."},
    "Saturn": {"day": "Saturday", "practice": "Observe a disciplined fast or simple meal with service, humility, and patience."},
    "Rahu": {"day": "Saturday", "practice": "Use Saturday restraint, simplicity, and grounding practices to settle Rahu's turbulence."},
    "Ketu": {"day": "Tuesday", "practice": "Take a simple fast with meditation, silence, and non-attachment practices."},
}

CHARITY_MAP = {
    "Sun": {"recommendation": "Donate wheat, jaggery, copper, or support fatherly figures, mentors, or public service work."},
    "Moon": {"recommendation": "Offer milk, rice, white clothing, or nourishment to mothers, women, or those needing emotional care."},
    "Mars": {"recommendation": "Donate red lentils or support injured people, emergency causes, or disciplined physical service."},
    "Mercury": {"recommendation": "Give green moong, stationery, books, or educational support for students and young learners."},
    "Jupiter": {"recommendation": "Donate turmeric, yellow foods, scriptures, or support teachers, priests, and education."},
    "Venus": {"recommendation": "Offer white sweets, clothing, beauty-care essentials, or support women in need."},
    "Saturn": {"recommendation": "Donate black sesame, blankets, footwear, or serve laborers, elders, or the chronically burdened."},
    "Rahu": {"recommendation": "Feed the poor, support addiction recovery or mental-health care, and reduce chaotic excess in life."},
    "Ketu": {"recommendation": "Feed stray dogs, support spiritual spaces, or give quietly without seeking recognition."},
}

RUDRAKSHA_MAP = {
    "Sun": {"name": "1 Mukhi Rudraksha", "recommendation": "Used for solar authority, vitality, and centered identity."},
    "Moon": {"name": "2 Mukhi Rudraksha", "recommendation": "Used for emotional balance, peace, and relational softness."},
    "Mars": {"name": "3 Mukhi Rudraksha", "recommendation": "Used for courage, energy balance, and directed will."},
    "Mercury": {"name": "4 Mukhi Rudraksha", "recommendation": "Used for speech, intellect, study, and mental order."},
    "Jupiter": {"name": "5 Mukhi Rudraksha", "recommendation": "Used for wisdom, guidance, and sattvic steadiness."},
    "Venus": {"name": "6 Mukhi Rudraksha", "recommendation": "Used for harmony, attraction, relationship grace, and refined pleasures."},
    "Saturn": {"name": "7 Mukhi Rudraksha", "recommendation": "Used for endurance, karmic balance, and patient discipline."},
    "Rahu": {"name": "8 Mukhi Rudraksha", "recommendation": "Used for grounding ambition, reducing confusion, and handling worldly turbulence."},
    "Ketu": {"name": "9 Mukhi Rudraksha", "recommendation": "Used for inner detachment, spiritual sharpness, and karmic release."},
}
