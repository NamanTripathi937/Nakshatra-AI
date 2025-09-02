from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from api.astrology import get_kundli_data
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.astrology import get_kundli_data
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
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

@app.get("/ping")
def ping():
    print("Ping received!")
    return {"status": "ok"}

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Send to LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=api_key
)

memory = ConversationBufferMemory()

conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)
today = datetime.now().strftime("%Y-%m-%d")
@app.post("/kundli")
async def kundli(request: Request):
    data = await request.json()

    kundli_data = get_kundli_data(data)

    user_message = data.get("message")

    # Prepare the system message for memory
    intro = f"""This is the user's Kundli data for reference during the chat:\n{kundli_data}"""

    # Add this system message to memory as if it was part of the conversation
    memory.chat_memory.add_user_message("My birth details")
    memory.chat_memory.add_ai_message(intro)

    # You can also get a response from the LLM, if you want
    prompt = f"""
    You are an expert astrologer analyzing a kundli. Follow these rules STRICTLY:
    1. NEVER show your reasoning process
    2. ONLY provide the final analysis
    Today is {today}
    Kundli Data:
    {kundli_data}
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
