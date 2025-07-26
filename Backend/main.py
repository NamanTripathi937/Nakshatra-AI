from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from api.astrology import get_kundli_data

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

kundli_data = get_kundli_data()

if not kundli_data:
    print("Failed to retrieve kundli data")
    exit()

# Prepare your prompt with STRICT instructions
prompt = f"""
You are an expert astrologer analyzing a kundli. Follow these rules STRICTLY:
1. NEVER include <think> or </think> blocks
2. NEVER show your reasoning process
3. ONLY provide the final analysis
4. Use markdown formatting with these exact section headings:
   - **1. Personality Traits**
   - **2. Current Planetary Influences**
   - **3. Notable Planetary Placements**
   - **4. Important Yogas/Doshas**

Birth Details:
- Date: 15-06-1989
- Time: 16:44
- Location: Latitude 28.98, Longitude 77.7, Timezone +5.5

Kundli Data:
{kundli_data}

Now provide the analysis following ALL rules above:
"""

# Send to LLM
llm = ChatGroq(
    model="deepseek-r1-distill-llama-70b",
    api_key=api_key
)

response = llm.invoke(prompt)

# Post-processing to ensure no think blocks remain
final_output = response.content.replace("<think>", "").replace("</think>", "").strip()
print(final_output)