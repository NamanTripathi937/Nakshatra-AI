import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from database import get_users_collection
from models import UserData
from auth import (
    GOOGLE_CLIENT_ID,
    build_auth_token_for_user,
    build_user_payload,
    verify_google_credential,
    utc_now,
)
from app.core.dependencies import get_current_user, refresh_user_account_state

logger = logging.getLogger("nakshatra-backend")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google")
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


@router.get("/me")
async def auth_me(request: Request):
    user_doc = await get_current_user(request)
    user_doc = await refresh_user_account_state(user_doc)
    return JSONResponse(content={"user": build_user_payload(user_doc)})
