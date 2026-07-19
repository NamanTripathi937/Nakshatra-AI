import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from database import get_sessions_collection
from models import SessionData
from auth import (
    build_plan_access,
    build_user_payload,
    utc_now,
)
from numerology import NumerologyInputError, build_numerology_profile
from app.core.dependencies import (
    get_current_user,
    refresh_user_account_state,
    get_owned_session_doc,
    serialize_message_doc,
    parse_session_history_limit,
    build_session_history_item,
)

logger = logging.getLogger("nakshatra-backend")

router = APIRouter(tags=["sessions"])


@router.post("/sessions")
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


@router.get("/sessions/{session_id}")
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


@router.get("/sessions")
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


@router.post("/numerology")
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
