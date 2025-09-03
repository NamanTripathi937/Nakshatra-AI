from langchain_groq import ChatGroq
import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.astrology import get_kundli_data
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev, use actual domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping") # To cold start backend as soon as frontend is opened
def ping():
    print("Ping received!")
    return {"status": "ok"}

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Send to LLM
llm = ChatGroq(
    model="openai/gpt-oss-20B",
    api_key=api_key
)

memory = ConversationBufferMemory(return_messages=True)

conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# Find current maha/antar dasha
def get_current_dasha(dasha_data: dict, today: datetime):
    try:
        for maha, antars in dasha_data.items():
            for antar, period in antars.items():
                try:
                    start = datetime.fromisoformat(period.get("start_time", ""))
                    end = datetime.fromisoformat(period.get("end_time", ""))
                except (ValueError, TypeError):
                    # Skip if invalid date format
                    continue

                if start <= today <= end:
                    return maha, antar
    except Exception as e:
        # Log or print error for debugging
        print(f"Error in get_current_dasha: {e}")

    return None, None


@app.post("/kundli")
async def kundli(request: Request):
    data = await request.json()
    kundli_data = get_kundli_data(data)

    # Parse dasha data safely
    dasha_json_str = kundli_data["Vimsottari Maha Dasas and Antar Dasas"]["output"]
    dasha_data = json.loads(dasha_json_str)

    today_dt = datetime.now()

        # Prepare the system message for memory
    intro = f"""This is the user's Kundli data for reference during the chat:\n{kundli_data}"""

    # Add this system message to memory as if it was part of the conversation
    memory.chat_memory.add_user_message("My birth details")
    memory.chat_memory.add_message(SystemMessage(content=intro))

    current_mahadasha, current_antardasha = get_current_dasha(dasha_data, today_dt)
    # ✅ Clean prompt for LLM
    prompt = f"""
    You are an expert astrologer with full access to the user's Kundli data 
    (including planetary placements and Vimsottari Dasha timeline).

    ### Core Rules
    1. NEVER ask the user for birth details (they are already included).
    2. DO NOT recalculate Mahadasha or Antardasha. Use the given data only.
    3. Dashas usage:
    - For personality, tendencies, general nature, life themes → use planetary placements only.
    - For time-based queries ("now", "next week", "this year", "future", "when will...") → use the current/relevant Mahadasha & Antardasha from the Kundli data.
    4. Responses must be **concise, crisp, and to the point** — highlight only the **major and interesting insights**.  
    - Do not give long or overly detailed breakdowns (e.g., no house-by-house descriptions unless explicitly asked).  
    - Avoid repetition and filler text.  
    5. Format:
    - Write in clean Markdown.
    - Use short paragraphs by default.
    - Use **bullet points** for clarity when summarizing.
    - Use tables **only if the user explicitly requests it**.  
    6. Word limit: Max 150–200 words. Never exceed.  

    ### Kundli Data
    {kundli_data}

    ### Today’s Context
    Date: {today_dt.strftime('%Y-%m-%d')}
    Current Mahadasha: {current_mahadasha}
    Current Antardasha: {current_antardasha}
    """
    response = llm.invoke(prompt)
    return {response.content.strip()}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    print("Received data in /chat:", data)

    response = conversation.predict(input=data["query"])

    return JSONResponse(content={"response": response.strip()})
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload    
# .\venv\Scripts\Activate.ps1  
