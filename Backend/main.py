from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from api.astrology import get_kundli_data
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.astrology import get_kundli_data

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev, use actual domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Send to LLM
llm = ChatGroq(
    model="llama3-70b-8192",
    api_key=api_key
)

@app.post("/kundli")
async def kundli(request: Request):
    payload = await request.json()

    # 1. Get kundli data from RapidAPI
    kundli_data =await get_kundli_data(payload)

    if not kundli_data:
        return {"error": "Failed to fetch kundli data"}

    # 2. Prepare prompt
    prompt = f"""
    You are an expert astrologer analyzing a kundli. Follow these rules STRICTLY:
    1. NEVER show your reasoning process
    2. ONLY provide the final analysis

    Kundli Data:
    {kundli_data}

    Now provide the analysis following ALL rules above:
    """

    # 3. Send prompt to Groq LLM
    response = llm.invoke(prompt)

    # 4. Return LLM output
    print("generated LLM response successfully", response.content)
    return {"analysis": response.content}