import os
from dotenv import load_dotenv

load_dotenv()
rapid_api_key = os.getenv("rapidapi-key")

import requests
import json

api_key = os.getenv("free-api-key")

#     payload = json.dumps({
#       "year": 2024,
#       "month": 6,
#       "date": 10,
#       "hours": 15,
#       "minutes": 10,
#       "seconds": 0,
#       "latitude": 18.9333,
#       "longitude": 72.8166,
#       "timezone": 5.5,
#       "settings": {
#           "observation_point": "topocentric",
#           "ayanamsha": "lahiri"
#       }
#   })

ENDPOINTS = {
    "main_planets": "https://json.apiastro.com/planets/extended",
    "navamsa": "https://json.freeastrologyapi.com/navamsa-chart-info",
    "d3": "https://json.freeastrologyapi.com/d3-chart-info",
    "d7": "https://json.freeastrologyapi.com/d7-chart-info",
    "d10": "https://json.freeastrologyapi.com/d10-chart-info"
}

headers = {
'Content-Type': 'application/json',
'x-api-key': api_key,
}

def get_kundli_data(payload):
    details = {}
    print("Raw payload from frontend:", payload)
    print("Types:", {k: type(v) for k, v in payload.items()})

    for key, url in ENDPOINTS.items():
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            details[key] = response.json()
        else:
            details[key] = {"error": f"Failed to fetch {key} data", "status": response.status_code}
    print(details)
    return details

