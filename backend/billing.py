import hashlib
import hmac
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "").strip()
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "").strip()

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"

PLAN_CATALOG: Dict[str, Dict[str, Any]] = {
    "addon_questions_10": {
        "code": "addon_questions_10",
        "kind": "addon_questions",
        "name": "Question Booster",
        "tagline": "10 extra questions whenever you need them",
        "description": "A one-time add-on that gives 10 extra AI questions on top of the free daily limit.",
        "amount_paise": 900,
        "currency": "INR",
        "question_credits": 10,
        "benefits": [
            "10 extra questions added to your account balance",
            "Works across future sessions until used",
            "Good for occasional deep follow-up readings",
        ],
        "badge": "One-time",
    },
    "premium_monthly": {
        "code": "premium_monthly",
        "kind": "membership",
        "name": "Premium Monthly",
        "tagline": "Full premium access for 30 days",
        "description": "Unlimited questions and all premium astrology tools for one month.",
        "amount_paise": 9900,
        "currency": "INR",
        "duration_days": 30,
        "benefits": [
            "Unlimited chat questions",
            "Detailed readings and richer chart reasoning",
            "D9 and D10 charts with insights",
            "Remedies, Kundli Milan, ad-free experience",
        ],
        "badge": "Most Complete",
    },
}


def is_razorpay_configured() -> bool:
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


def is_razorpay_webhook_configured() -> bool:
    return bool(RAZORPAY_WEBHOOK_SECRET)


def get_checkout_key_id() -> str:
    return RAZORPAY_KEY_ID


def format_inr_from_paise(amount_paise: int) -> str:
    rupees = amount_paise / 100
    if float(rupees).is_integer():
        return f"Rs. {int(rupees)}"
    return f"Rs. {rupees:.2f}"


def get_plan(code: str) -> Optional[Dict[str, Any]]:
    plan = PLAN_CATALOG.get(str(code or "").strip())
    if not plan:
        return None
    return {**plan}


def list_plans() -> List[Dict[str, Any]]:
    plans: List[Dict[str, Any]] = []
    for code in PLAN_CATALOG:
        plan = get_plan(code)
        if not plan:
            continue
        plans.append(
            {
                **plan,
                "display_price": format_inr_from_paise(plan["amount_paise"]),
            }
        )
    return plans


async def create_razorpay_order(*, amount_paise: int, currency: str, receipt: str, notes: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0, auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)) as client:
        response = await client.post(
            f"{RAZORPAY_API_BASE}/orders",
            json={
                "amount": int(amount_paise),
                "currency": currency,
                "receipt": receipt,
                "notes": notes or {},
            },
        )
    response.raise_for_status()
    return response.json()


async def fetch_razorpay_payment(payment_id: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0, auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)) as client:
        response = await client.get(f"{RAZORPAY_API_BASE}/payments/{payment_id}")
    response.raise_for_status()
    return response.json()


def verify_checkout_signature(order_id: str, payment_id: str, signature: str) -> bool:
    payload = f"{order_id}|{payment_id}"
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    expected = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
