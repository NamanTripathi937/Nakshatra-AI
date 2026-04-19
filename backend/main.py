import os
import json
import logging
import re
import time
from typing import Any, Dict, Optional
from datetime import datetime, timedelta, timezone
from threading import Lock
from contextlib import asynccontextmanager
from tempfile import TemporaryDirectory

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from pymongo import ReturnDocument
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
from langchain.schema import AIMessage, HumanMessage, SystemMessage

# from api.astrology import get_kundli_data // Can use freeastrologyapi.com to get kundli data
from astro.astro import (
    DEBILITATION_SIGNS,
    EXALTATION_SIGNS,
    MOOLATRIKONA_RANGES,
    OWN_SIGNS,
    generate_chart,
)
from auth import (
    DEFAULT_PLAN,
    GOOGLE_CLIENT_ID,
    build_auth_token_for_user,
    build_plan_access,
    build_user_payload,
    decode_auth_token,
    get_effective_plan,
    get_extra_questions_balance,
    get_premium_until,
    get_user_usage_snapshot,
    normalize_plan,
    utc_now,
    verify_google_credential,
)
from billing import (
    create_razorpay_order,
    fetch_razorpay_payment,
    get_checkout_key_id,
    get_plan,
    is_razorpay_webhook_configured,
    is_razorpay_configured,
    list_plans,
    verify_checkout_signature,
    verify_webhook_signature,
)
from database import connect_to_mongo, close_mongo_connection, get_payments_collection, get_sessions_collection, get_users_collection
from models import SessionData, Message, PaymentRecord, UserData
from numerology import NumerologyInputError, build_numerology_profile

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

CHART_EXPORT_SUMMARIES = {
    "D1": "The Lagna chart captures the natal foundation: temperament, life direction, and the main planetary framework.",
    "D9": "The Navamsha deepens the chart by showing dharma, marriage themes, and how planets mature over time.",
    "D10": "The Dashamsha focuses on vocation, visible karma, and how professional life tends to unfold.",
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


@app.post("/numerology")
async def numerology(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    full_name = (payload.get("fullName") or payload.get("full_name") or "").strip()
    date_of_birth = (payload.get("dateOfBirth") or payload.get("date_of_birth") or "").strip()

    if not date_of_birth:
        year = payload.get("year")
        month = payload.get("month")
        day = payload.get("date") or payload.get("day")
        if year is not None and month is not None and day is not None:
            try:
                date_of_birth = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Birth date fields must be valid numbers")

    try:
        result = build_numerology_profile(full_name, date_of_birth)
    except NumerologyInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return JSONResponse(content=result)


@app.post("/auth/google")
async def auth_google(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    credential = (payload.get("credential") or "").strip()
    if not credential:
        raise HTTPException(status_code=400, detail="Missing Google credential")
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured on the backend")

    try:
        google_profile = await verify_google_credential(credential)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    user_id = google_profile["google_sub"]
    now = utc_now()
    users_collection = get_users_collection()
    existing_user = await users_collection.find_one({"_id": user_id})

    if existing_user:
        await users_collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "email": google_profile["email"],
                    "name": google_profile["name"],
                    "picture": google_profile.get("picture"),
                    "updated_at": now,
                }
            },
        )
        user_doc = await users_collection.find_one({"_id": user_id})
    else:
        user_payload = UserData(
            google_sub=google_profile["google_sub"],
            email=google_profile["email"],
            name=google_profile["name"],
            picture=google_profile.get("picture"),
        ).dict()
        user_payload["_id"] = user_id
        await users_collection.insert_one(user_payload)
        user_doc = await users_collection.find_one({"_id": user_id})

    user_doc = await refresh_user_account_state(user_doc)
    token = build_auth_token_for_user(user_doc)
    return JSONResponse(content={"token": token, "user": build_user_payload(user_doc)})


@app.get("/auth/me")
async def auth_me(request: Request):
    user_doc = await get_current_user(request)
    user_doc = await refresh_user_account_state(user_doc)
    return JSONResponse(content={"user": build_user_payload(user_doc)})


@app.get("/billing/plans")
async def billing_plans(request: Request):
    user_doc = await get_current_user(request)
    user_doc = await refresh_user_account_state(user_doc)
    return JSONResponse(
        content={
            "configured": is_razorpay_configured(),
            "gateway": "razorpay",
            "plans": list_plans(),
            "user": build_user_payload(user_doc),
        }
    )


@app.post("/billing/checkout")
async def billing_checkout(request: Request):
    user_doc = await get_current_user(request)
    user_doc = await refresh_user_account_state(user_doc)

    if not is_razorpay_configured():
        raise HTTPException(status_code=503, detail="Billing is not configured on the backend yet.")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    plan_code = (payload.get("plan_code") or "").strip()
    plan = get_plan(plan_code)
    if not plan:
        raise HTTPException(status_code=404, detail="Unknown billing plan")

    now = utc_now()
    receipt = f"nk_{str(user_doc['_id'])[:8]}_{int(now.timestamp())}"
    notes = {
        "user_id": str(user_doc["_id"]),
        "email": user_doc.get("email") or "",
        "plan_code": plan["code"],
    }

    try:
        order = await create_razorpay_order(
            amount_paise=plan["amount_paise"],
            currency=plan["currency"],
            receipt=receipt,
            notes=notes,
        )
    except Exception:
        logger.exception("Failed to create Razorpay order for user %s", user_doc.get("email"))
        raise HTTPException(status_code=502, detail="Unable to start payment right now. Please try again in a moment.")

    payment_doc = PaymentRecord(
        order_id=order["id"],
        user_id=str(user_doc["_id"]),
        plan_code=plan["code"],
        plan_name=plan["name"],
        amount_paise=plan["amount_paise"],
        currency=plan["currency"],
        receipt=receipt,
        meta={
            "gateway_order": order,
            "user_email": user_doc.get("email"),
        },
    ).dict()
    payment_doc["_id"] = order["id"]
    await get_payments_collection().replace_one({"_id": order["id"]}, payment_doc, upsert=True)

    return JSONResponse(
        content={
            "plan": {**plan, "display_price": next((item["display_price"] for item in list_plans() if item["code"] == plan["code"]), "")},
            "checkout": {
                "key": get_checkout_key_id(),
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "name": "Nakshatra AI",
                "description": plan["tagline"],
                "prefill": {
                    "name": user_doc.get("name") or "",
                    "email": user_doc.get("email") or "",
                },
                "theme": {"color": "#0f6c7a"},
            },
        }
    )


@app.post("/billing/verify")
async def billing_verify(request: Request):
    user_doc = await get_current_user(request)
    user_doc = await refresh_user_account_state(user_doc)

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    order_id = (payload.get("razorpay_order_id") or "").strip()
    payment_id = (payload.get("razorpay_payment_id") or "").strip()
    signature = (payload.get("razorpay_signature") or "").strip()

    if not order_id or not payment_id or not signature:
        raise HTTPException(status_code=400, detail="Missing Razorpay verification fields")
    if not verify_checkout_signature(order_id, payment_id, signature):
        raise HTTPException(status_code=400, detail="Payment signature verification failed")

    payments_collection = get_payments_collection()
    payment_doc = await payments_collection.find_one({"_id": order_id, "user_id": str(user_doc["_id"])})
    if not payment_doc:
        raise HTTPException(status_code=404, detail="Payment record not found for this account")

    if payment_doc.get("activated") and payment_doc.get("fulfillment"):
        updated_user = await get_users_collection().find_one({"_id": user_doc["_id"]})
        updated_user = await refresh_user_account_state(updated_user)
        return JSONResponse(
            content={
                "success": True,
                "activation": payment_doc.get("fulfillment"),
                "user": build_user_payload(updated_user),
            }
        )

    try:
        provider_payment = await fetch_razorpay_payment(payment_id)
    except Exception:
        logger.exception("Failed to fetch Razorpay payment %s", payment_id)
        raise HTTPException(status_code=502, detail="Unable to verify payment right now. Please try again shortly.")

    if provider_payment.get("order_id") != order_id:
        raise HTTPException(status_code=400, detail="Payment does not belong to this order")
    if provider_payment.get("status") not in {"authorized", "captured"}:
        raise HTTPException(status_code=400, detail="Payment is not captured yet")

    fulfillment = await activate_paid_plan_for_user(
        user_doc=user_doc,
        payment_doc=payment_doc,
        payment_id=payment_id,
        provider_payment=provider_payment,
        source="checkout",
    )
    updated_user = await get_users_collection().find_one({"_id": user_doc["_id"]})
    updated_user = await refresh_user_account_state(updated_user)
    return JSONResponse(
        content={
            "success": True,
            "activation": fulfillment,
            "user": build_user_payload(updated_user),
        }
    )


@app.post("/billing/webhooks/razorpay")
async def razorpay_webhook(request: Request):
    if not is_razorpay_configured() or not is_razorpay_webhook_configured():
        return JSONResponse(content={"status": "ignored", "reason": "billing_not_configured"})

    signature = (request.headers.get("x-razorpay-signature") or "").strip()
    raw_body = await request.body()
    if not signature or not verify_webhook_signature(raw_body, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid webhook body")

    event = payload.get("event") or ""
    payment_entity = (((payload.get("payload") or {}).get("payment") or {}).get("entity") or {})
    order_id = payment_entity.get("order_id")
    payment_id = payment_entity.get("id")

    if event not in {"payment.authorized", "payment.captured"} or not order_id or not payment_id:
        return JSONResponse(content={"status": "ignored", "event": event})

    payments_collection = get_payments_collection()
    payment_doc = await payments_collection.find_one({"_id": order_id})
    if not payment_doc:
        return JSONResponse(content={"status": "ignored", "reason": "unknown_order"})
    if payment_doc.get("activated"):
        return JSONResponse(content={"status": "ok", "already_activated": True})

    user_doc = await get_users_collection().find_one({"_id": payment_doc.get("user_id")})
    if not user_doc:
        return JSONResponse(content={"status": "ignored", "reason": "unknown_user"})

    await activate_paid_plan_for_user(
        user_doc=user_doc,
        payment_doc=payment_doc,
        payment_id=payment_id,
        provider_payment=payment_entity,
        source="webhook",
    )
    return JSONResponse(content={"status": "ok"})


@app.post("/sessions")
async def create_session(request: Request):
    user_doc = await get_current_user(request)
    user_doc = await refresh_user_account_state(user_doc)
    now = utc_now()
    session_id = f"sess-{str(user_doc['_id'])[:8]}-{int(now.timestamp() * 1000)}"
    session_doc = SessionData(
        session_id=session_id,
        user_id=str(user_doc["_id"]),
        plan_snapshot=build_plan_access(user_doc)["plan"],
    ).dict()
    await get_sessions_collection().insert_one(session_doc)
    return JSONResponse(
        content={
            "session_id": session_id,
            "plan_access": build_plan_access(user_doc),
        }
    )


@app.get("/sessions/{session_id}")
async def get_session(request: Request, session_id: str):
    user_doc = await get_current_user(request)
    user_doc = await refresh_user_account_state(user_doc)
    session_doc = await get_owned_session_doc(
        str(user_doc["_id"]),
        session_id,
        {
            "session_id": 1,
            "full_name": 1,
            "birth_details": 1,
            "messages": 1,
            "updated_at": 1,
            "created_at": 1,
        },
    )
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found for this account")

    messages = [
        serialize_message_doc(message_doc, index)
        for index, message_doc in enumerate(session_doc.get("messages", []), start=1)
    ]
    return JSONResponse(
        content={
            "session_id": session_doc["session_id"],
            "full_name": session_doc.get("full_name"),
            "has_birth_details": bool(session_doc.get("birth_details")),
            "messages": messages,
            "plan_access": build_plan_access(user_doc),
        }
    )


@app.get("/sessions")
async def list_sessions(request: Request):
    user_doc = await get_current_user(request)
    session_limit = parse_session_history_limit(request.query_params.get("limit"))

    cursor = (
        get_sessions_collection()
        .find(
            {"user_id": str(user_doc["_id"])},
            {
                "session_id": 1,
                "full_name": 1,
                "birth_details": 1,
                "message_count": 1,
                "last_message_preview": 1,
                "last_message_role": 1,
                "created_at": 1,
                "updated_at": 1,
                "plan_snapshot": 1,
            },
        )
        .sort("updated_at", -1)
        .limit(session_limit)
    )
    session_docs = await cursor.to_list(length=session_limit)
    return JSONResponse(
        content={
            "sessions": [build_session_history_item(session_doc) for session_doc in session_docs],
            "plan_access": build_plan_access(user_doc),
        }
    )

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
) -> list[Any]:
    ordered = []
    if preferred_provider == "cerebras":
        ordered = [cerebras_provider, groq_provider]
    else:
        ordered = [groq_provider, cerebras_provider]
    return [provider for provider in ordered if provider and provider.enabled]


def invoke_with_failover(providers: list[Any], prompt: str, *, context: str) -> AIMessage:
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
        self.messages: list[Any] = []

    def add_message(self, message: Any) -> None:
        self.messages.append(message)

    def add_user_message(self, content: str) -> None:
        self.messages.append(HumanMessage(content=content))

    def add_ai_message(self, content: str) -> None:
        self.messages.append(AIMessage(content=content))


class SessionConversationState:
    def __init__(self) -> None:
        self.memory = type("MemoryContainer", (), {"chat_memory": SessionChatMemory()})()

# ----- Shared LLM client -----
groq_llm = LangChainProviderClient(
    "groq",
    ChatGroq(
        model="openai/gpt-oss-20B",
        api_key=GROQ_API_KEY,
        max_tokens=1400,
        timeout=90,
        max_retries=3,
    ) if GROQ_API_KEY else None,
)

groq_repair_llm = LangChainProviderClient(
    "groq",
    ChatGroq(
        model="openai/gpt-oss-20B",
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
_kundli_store: Dict[str, Dict[str, Any]] = {}
_kundli_lock = Lock()

_chain_store: Dict[str, SessionConversationState] = {}
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


def build_auth_error(message: str, status_code: int = 401, code: str = "unauthorized") -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def build_feature_lock_detail(feature: str, message: str, status_code: int = 403) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": "premium_required",
            "feature": feature,
            "message": message,
        },
    )


def extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("authorization") or ""
    prefix = "bearer "
    if not auth_header.lower().startswith(prefix):
        raise build_auth_error("Please sign in to continue.")
    token = auth_header[len(prefix):].strip()
    if not token:
        raise build_auth_error("Missing access token.")
    return token


async def get_current_user(request: Request) -> Dict[str, Any]:
    token = extract_bearer_token(request)
    try:
        payload = decode_auth_token(token)
    except ValueError as exc:
        raise build_auth_error(str(exc)) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise build_auth_error("Invalid access token payload.")

    users_collection = get_users_collection()
    user_doc = await users_collection.find_one({"_id": user_id})
    if not user_doc:
        raise build_auth_error("Account not found.", status_code=401)
    return user_doc


async def refresh_user_usage_if_needed(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    usage_snapshot = get_user_usage_snapshot(user_doc)
    current_usage = ((user_doc.get("usage") or {}).get("chat_daily") or {})
    if current_usage.get("date") != usage_snapshot["date"] or int(current_usage.get("count", 0) or 0) != usage_snapshot["count"]:
        user_doc["usage"] = {**(user_doc.get("usage") or {}), "chat_daily": usage_snapshot}
        await get_users_collection().update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"usage.chat_daily": usage_snapshot, "updated_at": utc_now()}},
        )
    return user_doc


async def refresh_user_billing_if_needed(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    effective_plan = get_effective_plan(user_doc)
    raw_plan = normalize_plan(user_doc.get("plan"))
    extra_balance = get_extra_questions_balance(user_doc)
    billing = user_doc.get("billing") or {}
    update_fields: Dict[str, Any] = {}

    if raw_plan != effective_plan:
        update_fields["plan"] = effective_plan
        user_doc["plan"] = effective_plan

    if int(billing.get("extra_questions_balance", 0) or 0) != extra_balance:
        update_fields["billing.extra_questions_balance"] = extra_balance
        user_doc["billing"] = {**billing, "extra_questions_balance": extra_balance}

    if update_fields:
        update_fields["updated_at"] = utc_now()
        await get_users_collection().update_one(
            {"_id": user_doc["_id"]},
            {"$set": update_fields},
        )
    return user_doc


async def refresh_user_account_state(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    user_doc = await refresh_user_billing_if_needed(user_doc)
    user_doc = await refresh_user_usage_if_needed(user_doc)
    return user_doc


async def activate_paid_plan_for_user(
    *,
    user_doc: Dict[str, Any],
    payment_doc: Dict[str, Any],
    payment_id: str,
    provider_payment: Optional[Dict[str, Any]] = None,
    source: str = "checkout",
) -> Dict[str, Any]:
    existing_fulfillment = payment_doc.get("fulfillment")
    if payment_doc.get("activated") and existing_fulfillment:
        return existing_fulfillment

    plan = get_plan(payment_doc.get("plan_code"))
    if not plan:
        raise HTTPException(status_code=404, detail="Billing plan not found for this payment")

    now = utc_now()
    users_collection = get_users_collection()
    payments_collection = get_payments_collection()
    claim_doc = await payments_collection.find_one_and_update(
        {"_id": payment_doc["_id"], "activated": {"$ne": True}},
        {
            "$set": {
                "status": "processing",
                "payment_id": payment_id,
                "provider_payment": provider_payment or {},
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.BEFORE,
    )
    if claim_doc is None:
        latest_doc = await payments_collection.find_one({"_id": payment_doc["_id"]})
        if latest_doc and latest_doc.get("fulfillment"):
            return latest_doc["fulfillment"]
        return {
            "type": "pending",
            "plan_code": payment_doc.get("plan_code"),
            "plan_name": payment_doc.get("plan_name"),
        }

    user_doc = await refresh_user_account_state(user_doc)
    billing = user_doc.get("billing") or {}

    user_set_fields: Dict[str, Any] = {
        "billing.last_payment_at": now,
        "billing.last_purchase_code": plan["code"],
        "billing.last_purchase_name": plan["name"],
        "updated_at": now,
    }
    user_inc_fields: Dict[str, Any] = {}
    fulfillment: Dict[str, Any]

    if plan["kind"] == "membership":
        active_until = get_premium_until(user_doc)
        premium_start = active_until if active_until and active_until > now else now
        premium_until = premium_start + timedelta(days=int(plan.get("duration_days", 30) or 30))
        user_set_fields.update(
            {
                "plan": "premium",
                "billing.premium_until": premium_until,
                "billing.active_membership_code": plan["code"],
                "billing.active_membership_name": plan["name"],
            }
        )
        fulfillment = {
            "type": "membership",
            "plan_code": plan["code"],
            "plan_name": plan["name"],
            "premium_until": serialize_datetime_value(premium_until),
            "activated_at": serialize_datetime_value(now),
            "source": source,
        }
    else:
        credits = int(plan.get("question_credits", 0) or 0)
        prior_balance = max(0, int(billing.get("extra_questions_balance", 0) or 0))
        user_inc_fields["billing.extra_questions_balance"] = credits
        fulfillment = {
            "type": "addon_questions",
            "plan_code": plan["code"],
            "plan_name": plan["name"],
            "question_credits_added": credits,
            "new_balance": prior_balance + credits,
            "activated_at": serialize_datetime_value(now),
            "source": source,
        }

    await users_collection.update_one(
        {"_id": user_doc["_id"]},
        {
            "$set": user_set_fields,
            **({"$inc": user_inc_fields} if user_inc_fields else {}),
        },
    )
    await payments_collection.update_one(
        {"_id": payment_doc["_id"]},
        {
            "$set": {
                "status": "paid",
                "activated": True,
                "payment_id": payment_id,
                "provider_payment": provider_payment or {},
                "paid_at": now,
                "updated_at": now,
                "fulfillment": fulfillment,
            }
        },
    )
    return fulfillment


async def ensure_daily_question_available(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    user_doc = await refresh_user_account_state(user_doc)
    plan_access = build_plan_access(user_doc)
    if not plan_access["is_premium"] and plan_access["daily_questions_remaining"] <= 0:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "daily_limit_reached",
                "message": "You have reached your 5 free questions for today. Upgrade to Premium for unlimited questions.",
            },
        )

    return user_doc


async def increment_daily_question_usage(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    user_doc = await ensure_daily_question_available(user_doc)
    plan_access = build_plan_access(user_doc)

    if plan_access["is_premium"]:
        return user_doc

    now = utc_now()
    free_remaining = int(plan_access.get("free_daily_questions_remaining") or 0)
    if free_remaining > 0:
        next_count = int(plan_access["daily_questions_used"]) + 1
        usage_payload = {"date": get_user_usage_snapshot(user_doc)["date"], "count": next_count}
        await get_users_collection().update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"usage.chat_daily": usage_payload, "updated_at": now}},
        )
        user_doc["usage"] = {**(user_doc.get("usage") or {}), "chat_daily": usage_payload}
        return user_doc

    extra_balance = get_extra_questions_balance(user_doc)
    if extra_balance > 0:
        await get_users_collection().update_one(
            {"_id": user_doc["_id"]},
            {"$inc": {"billing.extra_questions_balance": -1}, "$set": {"updated_at": now}},
        )
        billing = user_doc.get("billing") or {}
        user_doc["billing"] = {
            **billing,
            "extra_questions_balance": max(0, extra_balance - 1),
        }
        return user_doc

    return user_doc


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


async def save_assistant_message(
    *,
    user_id: str,
    session_id: str,
    message: str,
) -> None:
    try:
        sessions_collection = get_sessions_collection()
        assistant_message = Message(role="assistant", message=message)
        await sessions_collection.update_one(
            {"session_id": session_id, "user_id": user_id},
            {
                "$push": {"messages": assistant_message.dict()},
                "$inc": {"message_count": 1},
                "$set": {
                    "last_message_preview": truncate_preview(message),
                    "last_message_role": "assistant",
                    "updated_at": datetime.now(timezone.utc),
                },
            },
        )
        logger.info("Saved assistant message to MongoDB for session_id=%s", session_id)
    except Exception as exc:
        logger.exception("Failed to save assistant message to MongoDB (non-fatal): %s", exc)


async def get_owned_session_doc(
    user_id: str,
    session_id: str,
    projection: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    return await get_sessions_collection().find_one(
        {"session_id": session_id, "user_id": user_id},
        projection,
    )


async def get_authenticated_session(request: Request, projection: Optional[Dict[str, Any]] = None) -> tuple[Dict[str, Any], str, Dict[str, Any]]:
    user_doc = await get_current_user(request)
    session_id = request.headers.get("x-session-id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-Id header")

    session_doc = await get_owned_session_doc(str(user_doc["_id"]), session_id, projection)
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found for this account")
    return user_doc, session_id, session_doc


def serialize_message_doc(message_doc: Dict[str, Any], index: int) -> Dict[str, Any]:
    role = "ai" if message_doc.get("role") == "assistant" else "user"
    timestamp = message_doc.get("timestamp")
    return {
        "id": f"server-{index}",
        "sender": role,
        "content": message_doc.get("message", ""),
        "timestamp": serialize_datetime_value(timestamp),
    }


def serialize_datetime_value(value: Any) -> Optional[str]:
    if not hasattr(value, "isoformat"):
        return value
    dt_value = value
    if getattr(dt_value, "tzinfo", None) is None:
        dt_value = dt_value.replace(tzinfo=timezone.utc)
    return dt_value.isoformat()


def strip_markdown_for_preview(text: Optional[str]) -> str:
    cleaned = str(text or "")
    cleaned = re.sub(r"```[\s\S]*?```", " ", cleaned)
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"(^|\s)#{1,6}\s*", " ", cleaned)
    cleaned = re.sub(r"(\*\*|__|\*|_|~~)", "", cleaned)
    cleaned = re.sub(r"^[>\-\+\*]\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    return " ".join(cleaned.split())


def truncate_preview(text: Optional[str], limit: int = 140) -> str:
    cleaned = strip_markdown_for_preview(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def build_session_history_item(session_doc: Dict[str, Any]) -> Dict[str, Any]:
    messages = session_doc.get("messages") or []
    last_message = messages[-1] if messages else {}
    birth_details = session_doc.get("birth_details") or {}
    created_at = session_doc.get("created_at")
    updated_at = session_doc.get("updated_at")
    message_count = session_doc.get("message_count")
    if not isinstance(message_count, int):
        message_count = len(messages)

    last_message_preview = session_doc.get("last_message_preview")
    if not isinstance(last_message_preview, str):
        last_message_preview = truncate_preview(last_message.get("message"))

    last_message_role = session_doc.get("last_message_role")
    if not last_message_role:
        last_message_role = last_message.get("role")

    return {
        "session_id": session_doc.get("session_id"),
        "full_name": session_doc.get("full_name") or "Untitled Reading",
        "has_birth_details": bool(birth_details),
        "birth_date": (
            {
                "year": birth_details.get("year"),
                "month": birth_details.get("month"),
                "date": birth_details.get("date"),
            }
            if birth_details
            else None
        ),
        "message_count": message_count,
        "last_message_preview": last_message_preview,
        "last_message_role": last_message_role,
        "created_at": serialize_datetime_value(created_at),
        "updated_at": serialize_datetime_value(updated_at),
        "plan_snapshot": normalize_plan(session_doc.get("plan_snapshot")),
    }


def parse_session_history_limit(raw_limit: Optional[str], *, default: int = 24, maximum: int = 24) -> int:
    try:
        parsed = int(raw_limit or default)
    except (TypeError, ValueError):
        return default
    return max(1, min(parsed, maximum))


def format_birth_confirmation(payload: Dict[str, Any]) -> str:
    year = payload.get("year")
    month = payload.get("month")
    date = payload.get("date")
    hours = payload.get("hours")
    minutes = payload.get("minutes")
    seconds = payload.get("seconds", 0)
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    timezone_name = payload.get("timezone") or "Asia/Kolkata"
    settings = payload.get("settings") or {}

    lines = [
        "We have received your following Birth Details:",
        "",
        f"📅 Date of Birth: {date:02d} {datetime(2000, int(month), 1).strftime('%B')} {year}" if all(isinstance(v, int) for v in [year, month, date]) else "📅 Date of Birth: Provided",
        f"🕒 Time of Birth: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d} (24-hr)" if hours is not None and minutes is not None else "🕒 Time of Birth: Provided",
        f"🧾 ISO: {year}-{int(month):02d}-{int(date):02d}T{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}" if all(v is not None for v in [year, month, date, hours, minutes]) else "",
        f"📍 Coordinates: {float(latitude):.4f}° {'N' if float(latitude) >= 0 else 'S'}, {abs(float(longitude)):.4f}° {'E' if float(longitude) >= 0 else 'W'}" if latitude is not None and longitude is not None else "📍 Coordinates: Provided",
        f"⏰ Timezone: {timezone_name}",
    ]

    if settings:
        lines.append("⚙️ Settings:")
        for key, value in settings.items():
            label = str(key).replace("_", " ").title()
            lines.append(f"{label}: {value}")

    lines.extend(["", "Your details are saved privately to your account session so you can continue this reading securely ✅"])
    return "\n".join(line for line in lines if line != "")


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


def build_ashtakoot_breakdown(bride: Dict[str, Any], groom: Dict[str, Any]) -> list[Dict[str, Any]]:
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

    breakdown: list[Dict[str, Any]] = []
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


def build_compatibility_insights(breakdown: list[Dict[str, Any]]) -> Dict[str, Any]:
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


def summarize_current_dasha(kundli: Dict[str, Any]) -> str:
    current_line, _ = summarize_dasha_timeline(kundli)
    return current_line


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


def join_phrases(parts: list[str]) -> str:
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
    support_reasons: list[str] = []
    weakness_score = 0
    weakness_reasons: list[str] = []

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


def summarize_rule_based_remedies(kundli: Dict[str, Any]) -> list[str]:
    remedies = build_rule_based_remedies(kundli)
    lines: list[str] = []

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


def normalize_sign_for_jyotichart(sign_name: Optional[str]) -> Optional[str]:
    if not sign_name:
        return sign_name
    # jyotichart expects a misspelled Sagittarius string internally.
    if sign_name == "Sagittarius":
        return "Saggitarius"
    return sign_name


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

    chart_obj.set_ascendantsign(normalize_sign_for_jyotichart(asc_sign))
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


def get_chart_codes_for_plan(plan_access: Dict[str, Any]) -> list[str]:
    if plan_access["features"]["divisional_charts"]:
        return list(CHART_OPTIONS.keys())
    return ["D1"]


def build_chart_export_payload(
    kundli: Dict[str, Any],
    chart_code: str,
    style: str,
    details: list[Dict[str, Any]],
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
def ensure_chart_summary_in_memory(chain: SessionConversationState, chart_summary: str) -> None:
    if not chart_summary:
        return
    for message in chain.memory.chat_memory.messages:
        if isinstance(message, SystemMessage) and message.content.strip() == chart_summary.strip():
            return
    chain.memory.chat_memory.add_message(SystemMessage(content=chart_summary))


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


def build_chat_retry_fallback_response(user_query: str, kundli_available: bool) -> str:
    if kundli_available:
        return (
            "I hit a temporary issue while generating the full reply, but I still have your chart context. "
            "Please send the same question once more and I’ll continue with a chart-based answer."
        )
    return (
        "I hit a temporary issue while generating the reply. Please send the question once more and I’ll continue."
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

# To lot the metadata of each request for debugging
# @app.middleware("http")
# async def log_headers(request: Request, call_next):
#     sid = request.headers.get("x-session-id")
#     logger.info("REQ path=%s pid=%s X-Session-Id=%s", request.url.path, os.getpid(), sid)
#     return await call_next(request)


# ----- Helper to build the LLM prompt summary for kundli -----
def build_kundli_prompt(
    kundli: Dict[str, Any],
    profile: Optional[Dict[str, Any]],
    today: datetime,
    plan_access: Optional[Dict[str, Any]] = None,
) -> str:
    plan_access = plan_access or {}
    is_premium = bool(plan_access.get("is_premium"))
    response_style = build_response_style_instructions(is_first_message=True)
    reasoning_framework = build_astrology_reasoning_framework(is_first_message=True)
    chart_summary = (
        build_detailed_chart_summary(kundli, profile)
        if is_premium
        else build_free_tier_chart_summary(kundli, profile)
    )
    if is_premium:
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
    else:
        core_rules = (
            "You are writing the first free-tier reading inside Nakshatra AI after a user submits birth details.\n"
            "Use only the provided chart data and keep the experience warm, clear, and concise.\n\n"
            "### Free Tier Rules\n"
            "1. NEVER ask for birth details.\n"
            "2. Use only the natal chart and current dasha context. Do not rely on divisional charts, remedies, or premium extras.\n"
            "3. Keep this reading to 130 to 170 words.\n"
            "4. Focus on overall personality, one major strength, one growth theme, and the current chapter.\n"
            "5. End with a gentle note that deeper chart analysis is available in Premium.\n\n"
            "### Output Format\n"
            "## 🌌 Welcome to your Nakshatra AI reading, {first_name}\n"
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
{json.dumps({"full_name": (profile or {}).get("full_name"), "first_name": get_first_name((profile or {}).get("full_name"))}, indent=2)}

### Chart Context
{chart_summary}

### Today's Context
Date: {today.strftime('%Y-%m-%d')}
"""
    return prompt



def prune_memory_keep_last(chain: SessionConversationState, keep_last_pairs: int = 1):
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
    user_doc, session_id, _session_doc = await get_authenticated_session(request)
    plan_access = build_plan_access(user_doc)
    
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
    confirmation_message = Message(
        role="user",
        message=format_birth_confirmation(payload),
    )
    
    # Store session data in MongoDB
    try:
        sessions_collection = get_sessions_collection()
        full_name = payload.get("fullName", "Unknown")
        
        logger.info("Attempting to save kundli data: full_name=%s, session_id=%s", full_name, session_id)
        
        result = await sessions_collection.update_one(
            {"session_id": session_id, "user_id": str(user_doc["_id"])},
            {"$set": {
                "full_name": full_name,
                "birth_details": payload,
                "plan_snapshot": build_plan_access(user_doc)["plan"],
                "messages": [confirmation_message.dict()],
                "message_count": 1,
                "last_message_preview": truncate_preview(confirmation_message.message),
                "last_message_role": confirmation_message.role,
                "updated_at": datetime.now(timezone.utc),
            }}
        )
        logger.info("Initialized session with birth data for session_id=%s, matched=%s, modified=%s",
                    session_id, result.matched_count, result.modified_count)
    except Exception as e:
        logger.exception("Failed to save session data to MongoDB (non-fatal): %s", e)

    # Create or get the conversation chain for this session and add kundli as a system message in its memory
    chain = get_or_create_chain(session_id)
    try:
        ensure_chart_summary_in_memory(
            chain,
            chart_summary if plan_access["is_premium"] else build_free_tier_chart_summary(kundli, {"full_name": payload.get("fullName")}),
        )
    except Exception:
        # memory addition is not critical; log and continue
        logger.exception("Failed to add kundli to session memory (non-fatal)")

    # Optionally produce a short LLM summary of the kundli to return to the frontend
    try:
        prompt = build_kundli_prompt(
            kundli,
            {"full_name": payload.get("fullName")},
            datetime.now(),
            plan_access=plan_access,
        )
        llm_resp = invoke_with_failover(
            llm_providers,
            prompt,
            context="kundli summary generation",
        )
        summary_text = getattr(llm_resp, "content", str(llm_resp)).strip()
        summary_text = complete_if_truncated(summary_text)
    except Exception:
        logger.exception("LLM invoke failed for kundli summary; returning kundli without summary")
        summary_text = None

    try:
        await get_sessions_collection().update_one(
            {"session_id": session_id, "user_id": str(user_doc["_id"])},
            {
                "$push": {
                    "messages": Message(
                        role="assistant",
                        message=summary_text or "Kundli generated successfully.",
                    ).dict()
                },
                "$inc": {"message_count": 1},
                "$set": {
                    "last_message_preview": truncate_preview(summary_text or "Kundli generated successfully."),
                    "last_message_role": "assistant",
                    "updated_at": datetime.now(timezone.utc),
                },
            },
        )
    except Exception as e:
        logger.exception("Failed to save kundli response to MongoDB (non-fatal): %s", e)

    return JSONResponse(content={"response": summary_text or "Kundli generated successfully."})


@app.get("/charts")
async def charts(request: Request):
    user_doc, session_id, _session_doc = await get_authenticated_session(request)
    plan_access = build_plan_access(user_doc)

    chart_code = (request.query_params.get("code") or "D1").upper()
    style = (request.query_params.get("style") or "south").lower()

    if chart_code not in CHART_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported chart code: {chart_code}")
    if style not in CHART_STYLES:
        raise HTTPException(status_code=400, detail=f"Unsupported chart style: {style}")
    if chart_code != "D1" and not plan_access["features"]["divisional_charts"]:
        raise build_feature_lock_detail(
            "divisional_charts",
            "Navamsha and Dashamsha charts are available on Premium.",
        )

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


@app.get("/charts/export-data")
async def charts_export_data(request: Request):
    user_doc, session_id, session_doc = await get_authenticated_session(
        request,
        projection={"full_name": 1},
    )
    plan_access = build_plan_access(user_doc)
    style = (request.query_params.get("style") or "south").lower()

    if style not in CHART_STYLES:
        raise HTTPException(status_code=400, detail=f"Unsupported chart style: {style}")

    kundli = await get_or_restore_kundli(session_id)
    if not kundli:
        raise HTTPException(status_code=404, detail="Kundli not found for this session")

    chart_exports: list[Dict[str, Any]] = []
    for chart_code in get_chart_codes_for_plan(plan_access):
        try:
            details = build_chart_planet_details(kundli, chart_code)
            payload = build_chart_export_payload(kundli, chart_code, style, details)
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to build chart export payload for session_id=%s chart_code=%s", session_id, chart_code)
            raise HTTPException(status_code=500, detail="Failed to prepare chart export")
        chart_exports.append(payload)

    return JSONResponse(
        content={
            "name": (session_doc or {}).get("full_name") or "Untitled Reading",
            "session_id": session_id,
            "style": style,
            "plan": plan_access["plan"],
            "is_premium": plan_access["is_premium"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "charts": chart_exports,
        }
    )


@app.get("/remedies")
async def remedies(request: Request):
    user_doc, session_id, _session_doc = await get_authenticated_session(request)
    plan_access = build_plan_access(user_doc)
    if not plan_access["features"]["remedies"]:
        raise build_feature_lock_detail(
            "remedies",
            "Personalized remedies are a Premium feature.",
        )

    kundli = await get_or_restore_kundli(session_id)
    if not kundli:
        raise HTTPException(status_code=404, detail="Kundli not found for this session")

    try:
        remedies_payload = build_rule_based_remedies(kundli)
    except Exception:
        logger.exception("Failed to build remedies for session_id=%s", session_id)
        raise HTTPException(status_code=500, detail="Failed to build remedies")

    return JSONResponse(content=remedies_payload)


@app.post("/compatibility")
async def compatibility(request: Request):
    user_doc, session_id, _session_doc = await get_authenticated_session(request)
    plan_access = build_plan_access(user_doc)
    if not plan_access["features"]["compatibility"]:
        raise build_feature_lock_detail(
            "compatibility",
            "Kundli Milan is available on Premium.",
        )

    try:
        payload = await request.json()
    except Exception:
        logger.exception("Invalid JSON in /compatibility")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    native_role = normalize_match_role(payload.get("native_role"))
    partner_details = payload.get("partner") or {}
    if not partner_details:
        raise HTTPException(status_code=400, detail="Missing partner details in payload")

    try:
        sessions_collection = get_sessions_collection()
        session_doc = await sessions_collection.find_one(
            {"session_id": session_id, "user_id": str(user_doc["_id"])},
            {"birth_details": 1, "full_name": 1},
        )
    except Exception:
        logger.exception("Failed to load native birth data for compatibility session_id=%s", session_id)
        raise HTTPException(status_code=500, detail="Failed to load native birth details")

    native_birth_details = (session_doc or {}).get("birth_details")
    if not native_birth_details:
        raise HTTPException(status_code=404, detail="Native birth details not found for this session")

    try:
        native_kundli = get_kundli(session_id)
        if not native_kundli:
            native_kundli = json.loads(generate_chart(native_birth_details, house_system="WS"))
            store_kundli(session_id, native_kundli)

        partner_kundli = json.loads(generate_chart(partner_details, house_system="WS"))
        result = build_ashtakoot_match_response(
            native_kundli=native_kundli,
            partner_kundli=partner_kundli,
            native_name=(session_doc or {}).get("full_name") or "You",
            partner_name=partner_details.get("fullName") or "Partner",
            native_role=native_role,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to compute compatibility for session_id=%s", session_id)
        raise HTTPException(status_code=500, detail="Failed to compute compatibility")

    return JSONResponse(content=result)


@app.post("/chat")
async def chat(request: Request):
    """
    Chat endpoint:
    - Reads session id from header X-Session-Id (fallback 'default')
    - Looks up kundli for that session and appends it to the input prompt (if present)
    - Uses a per-session ConversationChain to keep chats isolated
    """
    user_doc, session_id, _session_doc = await get_authenticated_session(request)
    user_doc = await ensure_daily_question_available(user_doc)
    plan_access = build_plan_access(user_doc)

    try:
        payload = await request.json()
    except Exception:
        logger.exception("Invalid JSON in /chat")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    user_query = payload.get("query")
    if not user_query:
        raise HTTPException(status_code=400, detail="Missing 'query' in payload")

    logger.info("Received chat (session=%s user=%s): %s", session_id, user_doc.get("email"), user_query)

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
            {"session_id": session_id, "user_id": str(user_doc["_id"])},
            {
                "$push": {"messages": user_message.dict()},
                "$inc": {"message_count": 1},
                "$set": {
                    "last_message_preview": truncate_preview(user_query),
                    "last_message_role": "user",
                    "updated_at": datetime.now(timezone.utc),
                },
            },
        )
        logger.info("Saved user message to MongoDB for session_id=%s", session_id)
    except Exception as e:
        logger.exception("Failed to save user message to MongoDB (non-fatal): %s", e)

    # Attach preserved chart summary as system context when available.
    kundli = get_kundli(session_id)
    if not kundli:
        kundli = await get_or_restore_kundli(session_id)

    chart_summary = get_chart_summary(session_id)
    prompt_chart_summary = chart_summary
    if kundli:
        if not chart_summary:
            chart_summary = build_detailed_chart_summary(kundli)
            store_chart_summary(session_id, chart_summary)
        prompt_chart_summary = chart_summary if plan_access["is_premium"] else build_free_tier_chart_summary(kundli)
        ensure_chart_summary_in_memory(chain, prompt_chart_summary)
        response_style = build_response_style_instructions(user_query=user_query)
        reasoning_framework = build_astrology_reasoning_framework(user_query=user_query)
        premium_guidance = (
            "Answer directly and support your conclusions with the most relevant placements, house lords, yogas, aspects, dashas, or divisional-chart notes.\n"
            "Do not invent chart facts, yogas, dates, or remedies beyond the provided rule-based remedy notes.\n"
        )
        free_guidance = (
            "Keep the answer concise and practical.\n"
            "Use only natal-chart evidence plus the current dasha. Do not use divisional charts, remedies, compatibility scoring, transit predictions, or PDF-style report language.\n"
            "If the user asks for a Premium-only feature, briefly say it is unlocked on Premium.\n"
        )
        evidence_rules = (
            "Evidence rules:\n"
            "1. Do not answer in a generic self-help way.\n"
            "2. Explicitly mention at least two concrete astrological reasons from the chart, such as a planet in a sign/house, a house lord placement, a named yoga, an aspect, or the current dasha.\n"
            "3. When giving a conclusion, tie it back to those chart factors in plain language.\n"
            "4. For health questions, discuss astrological tendencies, vitality patterns, and vulnerable areas carefully, but do not present medical diagnosis or treatment.\n"
            "5. For friendship or social-circle questions, judge mainly through the 3rd and 11th houses and the relevant karakas instead of giving generic friendship advice.\n"
            "6. If chart context is unavailable, say so briefly instead of inventing an answer.\n"
        )
        final_input = (
            "You are a seasoned Vedic astrologer (Jyotishi).\n"
            "Use only the chart summary and recent conversation below.\n"
            f"{premium_guidance if plan_access['is_premium'] else free_guidance}"
            f"{evidence_rules}\n"
            f"{reasoning_framework}\n"
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
    prompt_payload = build_inline_chart_prompt(chain, prompt_chart_summary if kundli else None, final_input)
    resp_text = ""

    try:
        llm_resp = invoke_with_failover(
            llm_providers,
            prompt_payload,
            context="chat response generation",
        )
        resp_text = getattr(llm_resp, "content", str(llm_resp)).strip()
    except Exception:
        logger.warning("Primary chat invoke failed for session %s", session_id, exc_info=True)

    if not resp_text:
        try:
            retry_resp = invoke_with_failover(
                llm_providers,
                prompt_payload,
                context="chat retry generation",
            )
            resp_text = getattr(retry_resp, "content", str(retry_resp)).strip()
        except Exception:
            logger.warning("Retry chat invoke failed for session %s", session_id, exc_info=True)

    if not resp_text:
        fallback_prompt = (
            "You are a Vedic astrologer. Answer briefly but concretely using only the chart context provided. "
            "Mention at least two astrological reasons when chart context exists. "
            "If chart context is unavailable, say that briefly.\n\n"
            f"Chart Summary:\n{prompt_chart_summary if kundli and prompt_chart_summary else 'Chart context unavailable.'}\n\n"
            f"User Query: {user_query}"
        )
        try:
            repair_resp = invoke_with_failover(
                repair_llm_providers,
                fallback_prompt,
                context="chat repair generation",
            )
            resp_text = getattr(repair_resp, "content", str(repair_resp)).strip()
        except Exception:
            logger.warning("Repair chat invoke failed for session %s", session_id, exc_info=True)

    if resp_text:
        try:
            resp_text = complete_if_truncated(resp_text)
        except Exception:
            logger.warning("Truncation repair failed for session %s", session_id, exc_info=True)
    else:
        failure_message = build_no_credit_backend_failure_message(plan_access["is_premium"])
        logger.warning("Returning no-credit backend failure response for session %s after model failure", session_id)
        await save_assistant_message(
            user_id=str(user_doc["_id"]),
            session_id=session_id,
            message=failure_message,
        )
        raise HTTPException(
            status_code=503,
            detail={
                "code": "temporary_backend_failure_no_credit_used",
                "message": failure_message,
            },
        )

    user_doc = await increment_daily_question_usage(user_doc)

    try:
        chain.memory.chat_memory.add_user_message(user_query)
        chain.memory.chat_memory.add_ai_message(resp_text)
        prune_memory_keep_last(chain, keep_last_pairs=1)
    except Exception:
        logger.warning("Failed to update in-memory chat history for session %s", session_id, exc_info=True)
    
    await save_assistant_message(
        user_id=str(user_doc["_id"]),
        session_id=session_id,
        message=resp_text,
    )

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
