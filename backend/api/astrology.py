# This file was created in the earliest stages of the project and is not currently used.
# It can be used in future to fetch kundli data from freeastrologyapi.com
import os
from dotenv import load_dotenv
import requests
import json
import time

load_dotenv()
rapid_api_key = os.getenv("rapidapi-key")

api_key = os.getenv("free-api-key")
payload = {
    "year": 2003,
    "month": 5,
    "date": 7,
    "hours": 23,
    "minutes": 30,
    "seconds": 0,
    "latitude": 25.3708,
    "longitude": 86.4734,
    "timezone": 5.5,
    "config": {
        "observation_point": "topocentric",
        "ayanamsha": "lahiri"
    }
}

ENDPOINTS = {
    "main_planets": "https://json.apiastro.com/planets/extended",
    "navamsa": "https://json.freeastrologyapi.com/navamsa-chart-info",
   "d2": "https://json.freeastrologyapi.com/d2-chart-info",
  "d3": "https://json.freeastrologyapi.com/d3-chart-info",
  "d4": "https://json.freeastrologyapi.com/d4-chart-info",
  "d5": "https://json.freeastrologyapi.com/d5-chart-info",
  "d6": "https://json.freeastrologyapi.com/d6-chart-info",
  "d7": "https://json.freeastrologyapi.com/d7-chart-info",
  "d8": "https://json.freeastrologyapi.com/d8-chart-info",
  "d10": "https://json.freeastrologyapi.com/d10-chart-info",
  "d11": "https://json.freeastrologyapi.com/d11-chart-info",
  "d12": "https://json.freeastrologyapi.com/d12-chart-info",
  "d16": "https://json.freeastrologyapi.com/d16-chart-info",
  "d20": "https://json.freeastrologyapi.com/d20-chart-info",
  "d24": "https://json.freeastrologyapi.com/d24-chart-info",
  "d27": "https://json.freeastrologyapi.com/d27-chart-info",
  "d30": "https://json.freeastrologyapi.com/d30-chart-info",
  "d40": "https://json.freeastrologyapi.com/d40-chart-info",
  "d45": "https://json.freeastrologyapi.com/d45-chart-info",
  "d60": "https://json.freeastrologyapi.com/d60-chart-info",
    # "Vimsottari Maha Dasas and Antar Dasas" : "https://json.freeastrologyapi.com/vimsottari/maha-dasas-and-antar-dasas"
}

headers = {
'Content-Type': 'application/json',
'x-api-key': api_key,
}

def get_kundli_data(payload):
    details = {}
    for key, url in ENDPOINTS.items():
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            details[key] = response.json()
        else:
            details[key] = {
                "error": f"Failed to fetch {key} data",
                "status": response.status_code,
                "message": response.text
            }

        #Respect rate limit: sleep 1.1 sec
        time.sleep(1.1)
    print("Kundli details fetched:", details)
    return details


if __name__ == "__main__":
    get_kundli_data(payload)