import os
import httpx
from dotenv import load_dotenv
from services.scraper_service import extract_emails_from_website

# ===============================
# LOAD ENV
# ===============================
if os.path.exists(".env"):
    load_dotenv()

# ===============================
# CLEAN TEXT
# ===============================
def clean_text(text):
    if not text:
        return ""
    return str(text).encode("ascii", "ignore").decode("ascii")

# ===============================
# PLACE DETAILS
# ===============================
def get_place_details(place_id, api_key):
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "website",  # Pedimos únicamente el sitio web para máxima velocidad
            "key": api_key
        }
        response = httpx.get(url, params=params, timeout=10)
        data = response.json()
        return data.get("result", {})
    except Exception as e:
        print("DETAILS ERROR:", e)
        return {}

# ===============================
# SEARCH PLACES
# ===============================
def search_places(query, page_token=None):
    raw_api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    api_key = clean_text(raw_api_key).strip()
    clean_query = clean_text(query)

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": clean_query,
        "key": api_key
    }

    if page_token:
        params["pagetoken"] = page_token

    try:
        response = httpx.get(url, params=params, timeout=15)
        data = response.json()

        results = []
        raw_results = data.get("results", [])

        # CORRECCIÓN AQUÍ: Cambiamos el límite de [:5] a [:10] para que procese el paquete completo
        limit = min(25, len(raw_results))

        for i in range(limit):
            place = raw_results[i]
            place_id = place.get("place_id")

            # Traemos los detalles del lugar (Sitio Web)
            details = get_place_details(place_id, api_key)
            website = details.get("website", "")

            # Obtener correos reales si existe página web
            emails = []
            if website:
                emails = extract_emails_from_website(website)

            # Mapeo geométrico seguro para que el mapa pinte perfectamente
            geometry = place.get("geometry", {})
            location = geometry.get("location", {})

            results.append({
                "name": place.get("name", "Sin nombre"),
                "address": "No solicitada",
                "location": {
                    "lat": location.get("lat"),
                    "lng": location.get("lng")
                },
                "website": website,
                "phone": "No solicitado",
                "emails": emails
            })

        return {
            "results": results,
            "next_page_token": data.get("next_page_token")
        }

    except Exception as e:
        print("GOOGLE MAPS ERROR:", e)
        return {
            "results": [],
            "error": str(e)
        }
    