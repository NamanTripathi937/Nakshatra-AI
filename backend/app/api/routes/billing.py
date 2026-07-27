import json
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from database import get_users_collection, get_payments_collection
from models import PaymentRecord
from auth import (
    build_user_payload,
    utc_now,
)
from billing import (
    create_razorpay_order,
    fetch_razorpay_payment,
    get_checkout_key_id,
    get_plan,
    is_razorpay_configured,
    is_razorpay_webhook_configured,
    list_plans,
    verify_checkout_signature,
    verify_webhook_signature,
)
from app.core.dependencies import (
    get_current_user,
    refresh_user_account_state,
    activate_paid_plan_for_user,
)

logger = logging.getLogger("nakshatra-backend")

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans")
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


@router.post("/checkout")
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


@router.post("/verify")
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


@router.post("/webhooks/razorpay")
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
