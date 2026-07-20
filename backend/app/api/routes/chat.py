import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from database import get_sessions_collection
from models import Message
from astro.astro import generate_chart, enrich_kundli_with_current_gochar
from auth import build_plan_access

from app.core.dependencies import (
    get_authenticated_session,
    ensure_daily_question_available,
    increment_daily_question_usage,
    save_assistant_message,
    format_birth_confirmation,
    truncate_preview,
)
from app.services.astrology_service import (
    store_kundli,
    get_kundli,
    store_chart_summary,
    get_chart_summary,
    get_or_restore_kundli,
    build_detailed_chart_summary,
    build_free_tier_chart_summary,
    build_chart_planet_details,
    build_chart_export_payload,
    get_chart_codes_for_plan,
    build_rule_based_remedies,
    normalize_match_role,
    build_ashtakoot_match_response,
    get_chart_data_for_code,
)
from app.services.llm_service import (
    get_or_create_chain,
    ensure_chart_summary_in_memory,
    build_response_style_instructions,
    build_astrology_reasoning_framework,
    build_inline_chart_prompt,
    build_kundli_prompt,
    invoke_with_failover,
    llm_providers,
    repair_llm_providers,
    complete_if_truncated,
    build_no_credit_backend_failure_message,
    prune_memory_keep_last,
)
from app.services.chart_renderer import render_chart_svg
from app.core.constants import CHART_OPTIONS, CHART_STYLES

logger = logging.getLogger("nakshatra-backend")

router = APIRouter(tags=["chat"])


@router.post("/kundli")
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
        print("This is the payload", payload)
    except Exception:
        logger.exception("Invalid JSON in /kundli")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Generate the kundli
    try:
        kundli_data = json.loads(generate_chart(payload, house_system="WS"))
    except Exception:
        logger.exception("Failed to generate kundli")
        raise HTTPException(status_code=500, detail="Failed to generate kundli")

    # Store kundli per session (in memory)
    store_kundli(session_id, kundli_data)
    logger.info("Stored kundli for session_id=%s", session_id)
    chart_summary = build_detailed_chart_summary(kundli_data, {"full_name": payload.get("fullName")})
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
            chart_summary if plan_access["is_premium"] else build_free_tier_chart_summary(kundli_data, {"full_name": payload.get("fullName")}),
        )
    except Exception:
        # memory addition is not critical; log and continue
        logger.exception("Failed to add kundli to session memory (non-fatal)")

    # Optionally produce a short LLM summary of the kundli to return to the frontend
    try:
        prompt = build_kundli_prompt(
            kundli_data,
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


@router.post("/chat")
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
    kundli_data = get_kundli(session_id)
    if not kundli_data:
        kundli_data = await get_or_restore_kundli(session_id)

    chart_summary = get_chart_summary(session_id)
    prompt_chart_summary = chart_summary
    if kundli_data:
        kundli_data = enrich_kundli_with_current_gochar(kundli_data)
        store_kundli(session_id, kundli_data)

        chart_summary = build_detailed_chart_summary(kundli_data)
        store_chart_summary(session_id, chart_summary)
        prompt_chart_summary = chart_summary if plan_access["is_premium"] else build_free_tier_chart_summary(kundli_data)
        ensure_chart_summary_in_memory(chain, prompt_chart_summary)
        response_style = build_response_style_instructions(user_query=user_query)
        reasoning_framework = build_astrology_reasoning_framework(user_query=user_query)
        premium_guidance = (
            "Before giving the answer, judge the natal promise together with the current dasha and the current gochar.\n"
            "Answer directly and support your conclusions with the most relevant placements, house lords, yogas, aspects, dashas, gochar, or divisional-chart notes.\n"
            "Do not invent chart facts, yogas, dates, or remedies beyond the provided rule-based remedy notes.\n"
        )
        free_guidance = (
            "Keep the answer concise and practical.\n"
            "Before giving the answer, judge the natal promise together with the current dasha and the current gochar.\n"
            "Use natal-chart evidence, current dasha, and current gochar. Do not use divisional charts, remedies, compatibility scoring, or PDF-style report language.\n"
            "If the user asks for a Premium-only feature, briefly say it is unlocked on Premium.\n"
        )
        evidence_rules = (
            "Evidence rules:\n"
            "1. Do not answer in a generic self-help way.\n"
            "2. Explicitly mention at least two concrete astrological reasons from the chart, such as a planet in a sign/house, a house lord placement, a named yoga, an aspect, the current dasha, or the current gochar.\n"
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
    prompt_payload = build_inline_chart_prompt(chain, prompt_chart_summary if kundli_data else None, final_input)
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
            f"Chart Summary:\n{prompt_chart_summary if kundli_data and prompt_chart_summary else 'Chart context unavailable.'}\n\n"
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


@router.get("/charts")
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
        from app.core.dependencies import build_feature_lock_detail
        raise build_feature_lock_detail(
            "divisional_charts",
            "Navamsha and Dashamsha charts are available on Premium.",
        )

    kundli_data = await get_or_restore_kundli(session_id)
    if not kundli_data:
        raise HTTPException(status_code=404, detail="Kundli not found for this session")

    try:
        chart_data = get_chart_data_for_code(kundli_data, chart_code)
        svg = render_chart_svg(
            kundli_data,
            chart_code=chart_code,
            style=style,
            person_name=session_id,
        )
        details = build_chart_planet_details(kundli_data, chart_code)
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


@router.get("/charts/export-data")
async def charts_export_data(request: Request):
    user_doc, session_id, session_doc = await get_authenticated_session(
        request,
        projection={"full_name": 1},
    )
    plan_access = build_plan_access(user_doc)
    style = (request.query_params.get("style") or "south").lower()

    if style not in CHART_STYLES:
        raise HTTPException(status_code=400, detail=f"Unsupported chart style: {style}")

    kundli_data = await get_or_restore_kundli(session_id)
    if not kundli_data:
        raise HTTPException(status_code=404, detail="Kundli not found for this session")

    export_payload = {
        **kundli_data,
        "name": (session_doc or {}).get("full_name") or "Untitled Reading",
        "session_id": session_id,
        "style": style,
        "plan": plan_access["plan"],
        "is_premium": plan_access["is_premium"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    return JSONResponse(content=export_payload)


@router.get("/remedies")
async def remedies(request: Request):
    user_doc, session_id, _session_doc = await get_authenticated_session(request)
    plan_access = build_plan_access(user_doc)
    if not plan_access["features"]["remedies"]:
        from app.core.dependencies import build_feature_lock_detail
        raise build_feature_lock_detail(
            "remedies",
            "Personalized remedies are a Premium feature.",
        )

    kundli_data = await get_or_restore_kundli(session_id)
    if not kundli_data:
        raise HTTPException(status_code=404, detail="Kundli not found for this session")

    try:
        remedies_payload = build_rule_based_remedies(kundli_data)
    except Exception:
        logger.exception("Failed to build remedies for session_id=%s", session_id)
        raise HTTPException(status_code=500, detail="Failed to build remedies")

    return JSONResponse(content=remedies_payload)


@router.post("/compatibility")
async def compatibility(request: Request):
    user_doc, session_id, _session_doc = await get_authenticated_session(request)
    plan_access = build_plan_access(user_doc)
    if not plan_access["features"]["compatibility"]:
        from app.core.dependencies import build_feature_lock_detail
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
