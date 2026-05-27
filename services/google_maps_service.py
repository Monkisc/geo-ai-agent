import requests
import os
import time

from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# ===============================
# BUSCAR LUGARES
# ===============================
def search_places(query, page_token=None):

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    params = {
        "query": query,
        "key": GOOGLE_MAPS_API_KEY
    }

    # IMPORTANTE PARA PAGINACIÓN
    if page_token:

        time.sleep(2)

        params["pagetoken"] = page_token

    response = requests.get(url, params=params)

    data = response.json()

    results = []

    for place in data.get("results", []):

        results.append({

            "name": place.get("name"),

            "address": place.get("formatted_address"),

            "location": place.get("geometry", {}).get("location"),

            "rating": place.get("rating"),

            "types": place.get("types", []),

        })

    return {
        "results": results,
        "next_page_token": data.get("next_page_token")
    }
