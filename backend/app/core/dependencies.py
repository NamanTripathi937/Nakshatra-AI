import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Request, HTTPException
from pymongo import ReturnDocument

from database import get_users_collection, get_sessions_collection, get_payments_collection
from models import UserData, Message, PaymentRecord
from auth import (
    decode_auth_token,
    build_auth_token_for_user,
    build_plan_access,
    get_premium_until,
    get_extra_questions_balance,
    get_user_usage_snapshot,
    normalize_plan,
    get_effective_plan,
    utc_now,
    build_user_payload,
)
from billing import get_plan

logger = logging.getLogger("nakshatra-backend")

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
