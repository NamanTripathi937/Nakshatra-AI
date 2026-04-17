import base64
import hashlib
import hmac
import json
import math
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

FREE_DAILY_QUESTIONS = 5
DEFAULT_PLAN = "free"
PREMIUM_PLAN = "premium"
TOKEN_LIFETIME_DAYS = 14

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
APP_AUTH_SECRET = (
    os.getenv("APP_AUTH_SECRET")
    or os.getenv("JWT_SECRET")
    or os.getenv("GROQ_API_KEY")
    or "nakshatra-dev-secret"
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def today_key(now: Optional[datetime] = None) -> str:
    return (now or utc_now()).date().isoformat()


def normalize_plan(plan: Optional[str]) -> str:
    return PREMIUM_PLAN if str(plan or "").strip().lower() == PREMIUM_PLAN else DEFAULT_PLAN


def _coerce_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value.strip():
        try:
            dt_value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return dt_value if dt_value.tzinfo else dt_value.replace(tzinfo=timezone.utc)
    return None


def serialize_datetime(value: Optional[datetime]) -> Optional[str]:
    if not value:
        return None
    dt_value = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return dt_value.isoformat()


def get_billing_payload(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    return user_doc.get("billing") or {}


def get_extra_questions_balance(user_doc: Dict[str, Any]) -> int:
    billing = get_billing_payload(user_doc)
    return max(0, int(billing.get("extra_questions_balance", 0) or 0))


def get_premium_until(user_doc: Dict[str, Any]) -> Optional[datetime]:
    billing = get_billing_payload(user_doc)
    return _coerce_datetime(billing.get("premium_until"))


def get_premium_days_remaining(user_doc: Dict[str, Any], now: Optional[datetime] = None) -> Optional[int]:
    current_time = now or utc_now()
    premium_until = get_premium_until(user_doc)
    if premium_until is None or premium_until <= current_time:
        return None
    remaining_seconds = (premium_until - current_time).total_seconds()
    return max(1, math.ceil(remaining_seconds / 86400))


def get_effective_plan(user_doc: Dict[str, Any], now: Optional[datetime] = None) -> str:
    current_time = now or utc_now()
    premium_until = get_premium_until(user_doc)
    if premium_until is not None:
        return PREMIUM_PLAN if premium_until > current_time else DEFAULT_PLAN
    return normalize_plan(user_doc.get("plan"))


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def sign_auth_token(payload: Dict[str, Any]) -> str:
    body = base64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = hmac.new(
        APP_AUTH_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{body}.{base64url_encode(signature)}"


def decode_auth_token(token: str) -> Dict[str, Any]:
    try:
        body, provided_signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Malformed auth token") from exc

    expected_signature = base64url_encode(
        hmac.new(
            APP_AUTH_SECRET.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    )
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise ValueError("Invalid auth token signature")

    payload = json.loads(base64url_decode(body).decode("utf-8"))
    exp = int(payload.get("exp", 0) or 0)
    if exp and exp < int(utc_now().timestamp()):
        raise ValueError("Auth token expired")
    return payload


def build_auth_token_for_user(user_doc: Dict[str, Any]) -> str:
    now = utc_now()
    payload = {
        "sub": str(user_doc["_id"]),
        "email": user_doc.get("email"),
        "name": user_doc.get("name"),
        "plan": get_effective_plan(user_doc, now),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=TOKEN_LIFETIME_DAYS)).timestamp()),
    }
    return sign_auth_token(payload)


async def verify_google_credential(credential: str) -> Dict[str, Any]:
    if not GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID is not configured on the backend")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": credential},
        )

    if response.status_code != 200:
        raise ValueError("Invalid Google credential")

    data = response.json()
    audience = data.get("aud")
    issuer = data.get("iss")
    email_verified = data.get("email_verified")

    if audience != GOOGLE_CLIENT_ID:
        raise ValueError("Google credential audience mismatch")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise ValueError("Google credential issuer mismatch")
    if email_verified not in {True, "true"}:
        raise ValueError("Google account email is not verified")

    return {
        "google_sub": data.get("sub"),
        "email": (data.get("email") or "").strip().lower(),
        "name": data.get("name") or data.get("given_name") or "Nakshatra User",
        "picture": data.get("picture"),
    }


def get_user_usage_snapshot(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    usage = user_doc.get("usage") or {}
    daily = usage.get("chat_daily") or {}
    key = today_key()
    if daily.get("date") != key:
        return {"date": key, "count": 0}
    return {
        "date": key,
        "count": int(daily.get("count", 0) or 0),
    }


def build_plan_access(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    plan = get_effective_plan(user_doc)
    usage = get_user_usage_snapshot(user_doc)
    used = int(usage.get("count", 0) or 0)
    extra_question_balance = get_extra_questions_balance(user_doc)
    is_premium = plan == PREMIUM_PLAN
    free_remaining = max(0, FREE_DAILY_QUESTIONS - used)
    remaining = None if is_premium else free_remaining + extra_question_balance

    return {
        "plan": plan,
        "is_premium": is_premium,
        "ads_enabled": not is_premium,
        "daily_questions_limit": None if is_premium else FREE_DAILY_QUESTIONS + extra_question_balance,
        "daily_questions_used": used,
        "daily_questions_remaining": remaining,
        "free_daily_questions_remaining": None if is_premium else free_remaining,
        "extra_questions_balance": None if is_premium else extra_question_balance,
        "features": {
            "basic_kundli_summary": True,
            "full_detailed_readings": is_premium,
            "divisional_charts": is_premium,
            "remedies": is_premium,
            "compatibility": is_premium,
            "daily_transits": is_premium,
            "pdf_report": is_premium,
        },
    }


def build_user_payload(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    premium_until = get_premium_until(user_doc)
    premium_days_remaining = get_premium_days_remaining(user_doc)
    billing = get_billing_payload(user_doc)
    return {
        "id": str(user_doc["_id"]),
        "name": user_doc.get("name") or "Nakshatra User",
        "email": user_doc.get("email"),
        "picture": user_doc.get("picture"),
        "plan_access": build_plan_access(user_doc),
        "billing": {
            "premium_until": serialize_datetime(premium_until),
            "has_active_premium": bool(premium_until and premium_until > utc_now()),
            "premium_days_remaining": premium_days_remaining,
            "extra_questions_balance": get_extra_questions_balance(user_doc),
            "active_membership_code": billing.get("active_membership_code"),
            "active_membership_name": billing.get("active_membership_name"),
            "last_purchase_code": billing.get("last_purchase_code"),
            "last_purchase_name": billing.get("last_purchase_name"),
            "last_payment_at": serialize_datetime(_coerce_datetime(billing.get("last_payment_at"))),
        },
    }
