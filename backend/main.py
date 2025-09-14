# main.py
import os
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from threading import Lock

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage

from api.astrology import get_kundli_data
from astro.astro import generate_chart

# ----- Logging -----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nakshatra-backend")

# ----- App -----
app = FastAPI(title="Nakshatra AI Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    """Used by frontend to cold-start backend."""
    logger.info("Ping received")
    return {"status": "ok"}

# ----- Load env and validate -----
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY is not set")
    raise RuntimeError("GROQ_API_KEY environment variable is required")

# ----- Shared LLM client -----
llm = ChatGroq(model="openai/gpt-oss-20B", api_key=GROQ_API_KEY)

# ----- Per-session stores (thread-safe) -----
_kundli_store: Dict[str, Dict[str, Any]] = {}
_kundli_lock = Lock()

_chain_store: Dict[str, ConversationChain] = {}
_chain_lock = Lock()


def store_kundli(session_id: str, kundli: Dict[str, Any]) -> None:
    with _kundli_lock:
        _kundli_store[session_id] = kundli


def get_kundli(session_id: str) -> Optional[Dict[str, Any]]:
    with _kundli_lock:
        return _kundli_store.get(session_id)


def create_chain_for_session(session_id: str) -> ConversationChain:
    """
    Create a new ConversationChain with its own memory for a session.
    """
    memory = ConversationBufferMemory(llm=llm, return_messages=True)
    chain = ConversationChain(llm=llm, memory=memory, verbose=False)
    return chain


def get_or_create_chain(session_id: str) -> ConversationChain:
    with _chain_lock:
        chain = _chain_store.get(session_id)
        if chain is None:
            chain = create_chain_for_session(session_id)
            _chain_store[session_id] = chain
            logger.info("Created new conversation chain for session: %s", session_id)
        return chain


# ----- Helper to build the LLM prompt summary for kundli -----
def build_kundli_prompt(kundli: Dict[str, Any], today: datetime) -> str:
    core_rules = (
        "You are an expert astrologer with full access to the user's Kundli data "
        "(including planetary placements and Vimsottari Dasha timeline).\n\n"
        "### Core Rules\n"
        "1. NEVER ask the user for birth details (they are already included).\n"
        "2. DO NOT recalculate Mahadasha or Antardasha. Use the given data only.\n"
        "3. For personality/tendencies use planetary placements; for time-based queries use dashas.\n"
        "4. Responses must be concise and highlight only major insights.\n"
        "5. Output in clean Markdown; bullet points for summaries; tables only if requested.\n"
        "6. Word limit: Max 150 words.\n\n"
    )

    prompt = f"""{core_rules}
### Kundli Data
{json.dumps(kundli, indent=2)}

### Today's Context
Date: {today.strftime('%Y-%m-%d')}
"""
    return prompt


# ----- Endpoints -----


@app.post("/kundli")
async def kundli(request: Request):
    """
    Generate & store kundli for a session.
    Expects a JSON body with the birth details required by generate_chart.
    Session id is read from header 'X-Session-Id' (fallback to 'default').
    """
    session_id = request.headers.get("x-session-id", "default")
    try:
        payload = await request.json()
    except Exception:
        logger.exception("Invalid JSON in /kundli")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Generate the kundli (your generate_chart or get_kundli_data wrapper)
    try:
        kundli = generate_chart(payload, house_system="WS")
    except Exception:
        logger.exception("Failed to generate kundli")
        raise HTTPException(status_code=500, detail="Failed to generate kundli")

    # Store kundli per session
    store_kundli(session_id, kundli)
    logger.info("Stored kundli for session_id=%s", session_id)

    # Create or get the conversation chain for this session and add kundli as a system message in its memory
    chain = get_or_create_chain(session_id)
    try:
        intro = f"This is the user's Kundli data for reference during the chat:\n{json.dumps(kundli)}"
        # Add a system-style message into the session's memory so the chain can use it later
        # Use SystemMessage so it's distinguishable in memory
        chain.memory.chat_memory.add_user_message("My birth details")
        chain.memory.chat_memory.add_message(SystemMessage(content=intro))
    except Exception:
        # memory addition is not critical; log and continue
        logger.exception("Failed to add kundli to session memory (non-fatal)")

    # Optionally produce a short LLM summary of the kundli to return to the frontend
    try:
        prompt = build_kundli_prompt(kundli, datetime.now())
        llm_resp = llm.invoke(prompt)
        summary_text = getattr(llm_resp, "content", str(llm_resp)).strip()
    except Exception:
        logger.exception("LLM invoke failed for kundli summary; returning kundli without summary")
        summary_text = None

    return {llm_resp.content.strip()}


@app.post("/chat")
async def chat(request: Request):
    """
    Chat endpoint:
    - Reads session id from header X-Session-Id (fallback 'default')
    - Looks up kundli for that session and appends it to the input prompt (if present)
    - Uses a per-session ConversationChain to keep chats isolated
    """
    session_id = request.headers.get("x-session-id", "default")

    try:
        payload = await request.json()
    except Exception:
        logger.exception("Invalid JSON in /chat")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    user_query = payload.get("query")
    if not user_query:
        raise HTTPException(status_code=400, detail="Missing 'query' in payload")

    logger.info("Received chat (session=%s): %s", session_id, user_query)

    # get or create chain for session
    chain = get_or_create_chain(session_id)

    # append kundli if available for the session (keep a compact snippet)
    kundli = get_kundli(session_id)
    if kundli:
        # Attach kundli JSON as compact string to control token usage
        kundli_str = json.dumps(kundli)
        final_input = (
            f"User Query: {user_query}\n\n### Reference Kundli Data (do not recalculate):\n{kundli_str}"
        )
    else:
        final_input = user_query

    # run the conversation chain
    try:
        # Note: ConversationChain.predict may be synchronous depending on LangChain adapter
        resp_text = chain.predict(input=final_input).strip()
    except Exception:
        logger.exception("ConversationChain failed for session %s", session_id)
        raise HTTPException(status_code=500, detail="LLM conversation failed")

    return JSONResponse(content={"response": resp_text})

# uvicorn main:app --host 0.0.0.0 --port 8000 --reload    
# .\venv\Scripts\Activate.ps1  
