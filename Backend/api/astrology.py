import os
from dotenv import load_dotenv
import requests
import httpx
import json

load_dotenv()
rapid_api_key = os.getenv("rapidapi-key")

url = "https://kundli-pro.p.rapidapi.com/"

headers = {
    "x-rapidapi-key": rapid_api_key,
    "x-rapidapi-host": "kundli-pro.p.rapidapi.com",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"  
}

# payload = {
#     "birthdate": "15-06-1989",
#     "birthtime": "16:44",
#     "birthlongitude": "77.7",
#     "birthlatitude": "28.98",
#     "birthtimezone": "5.5"
# }

def extract_essential_kundli_data(full_response):
    """Extract only the essential astrological data needed for most queries"""
    try:
        data = json.loads(full_response)
    except json.JSONDecodeError:
        return full_response  # return as-is if not JSON
    
    essential_data = {
        "birth_details": data.get("birth_details", {}),
        "birth_panchang": data.get("birth_panchang", {}),
        "lagna_rashi": data.get("lagna_rashi", ""),
        "lagna_text": data.get("lagna_text", ""),
        "chandra_rashi": data.get("chandra_rashi", ""),
        "moonsign_text": data.get("moonsign_text", ""),
        "planet_details": {},
        "current_dasha": None,
        "important_yogas": {}
    }
    
    # Simplify planet details
    planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "rahu", "ketu"]
    for planet in planets:
        if planet in data.get("planet_details", {}):
            planet_data = data["planet_details"][planet]
            essential_data["planet_details"][planet] = {
                "house": planet_data.get("house", ""),
                "sign": planet_data.get("longitude_converted", "").split()[2] if planet_data.get("longitude_converted") else "",
                "nakshtra": planet_data.get("nakshtra", ""),
                "nakshtra_lord": planet_data.get("nakshtra_lord", ""),
                "motion": planet_data.get("motion", "")
            }
    
    # Get current dasha period
    vimshottari = data.get("vimshottari", {})
    for i in range(1, 10):
        major_key = f"major{i}"
        if major_key in vimshottari:
            major = vimshottari[major_key]
            start_date = major.get("start_date", "")
            end_date = major.get("end_date", "")
            if start_date and end_date:
                # Simple check if current date is between start and end (in real app, use datetime comparison)
                essential_data["current_dasha"] = {
                    "lord": major.get("lord", ""),
                    "start_date": start_date,
                    "end_date": end_date
                }
                break
    
    # Important yogas/doshas
    yoga_data = data.get("planet_combinations", {})
    essential_data["important_yogas"] = {
        "sadesati": yoga_data.get("sadesati", {}).get("status", ""),
        "manglik": yoga_data.get("manglik", {}).get("status", ""),
        "kaalsarp": yoga_data.get("kaalsarp", {}).get("status", "")
    }
    
    return json.dumps(essential_data, indent=2)

async def get_kundli_data(payload):
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Kundli data retrieved successfully", response.text)
            return extract_essential_kundli_data(response.text)
        return None