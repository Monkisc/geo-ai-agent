import os
import httpx
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()

def clean_text(text):
    if not text:
        return ""
    return str(text).encode("ascii", "ignore").decode("ascii")

def get_place_details(place_id, api_key):
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {"place_id": place_id, "fields": "website", "key": api_key}
        response = httpx.get(url, params=params, timeout=10)
        return response.json().get("result", {})
    except Exception as e:
        print(f"[get_place_details] Error: {e}")
        return {}

def search_places_page(query, api_key, offset=0):
    """
    Hace una búsqueda de texto con variaciones para simular paginación.
    offset 0 = primera página, offset 1 = segunda, offset 2 = tercera
    """
    clean_query = clean_text(query)
    
    # Para paginar sin usar pagetoken, usamos búsquedas ligeramente distintas
    # combinando el query con modificadores de ubicación más específicos
    suffixes = ["", " zona norte", " zona sur"]
    suffix = suffixes[offset % len(suffixes)] if offset > 0 else ""
    final_query = clean_query + suffix

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": final_query,
        "key": api_key,
        "language": "es",
    }

    try:
        response = httpx.get(url, params=params, timeout=15)
        data = response.json()
        status = data.get("status")
        raw_results = data.get("results", [])
        print(f"[search_places_page] offset={offset} Status: {status} | Resultados: {len(raw_results)}")
        return raw_results
    except Exception as e:
        print(f"[search_places_page] Error: {e}")
        return []

def search_places(query, page_token=None):
    """
    Devuelve 10 lugares por página.
    page_token aquí es un offset numérico (0, 1, 2...) no el token de Google.
    """
    raw_api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    api_key = clean_text(raw_api_key).strip()

    # Convertir page_token a offset numérico
    try:
        offset = int(page_token) if page_token else 0
    except (ValueError, TypeError):
        offset = 0

    raw_results = search_places_page(query, api_key, offset)

    results = []
    seen_ids = set()
    limit = min(20, len(raw_results))

    for i in range(limit):
        place = raw_results[i]
        place_id = place.get("place_id")
        
        if place_id in seen_ids:
            continue
        seen_ids.add(place_id)

        details  = get_place_details(place_id, api_key)
        website  = details.get("website", "")

        geometry = place.get("geometry", {})
        location = geometry.get("location", {})

        results.append({
            "name":     place.get("name", "Sin nombre"),
            "place_id": place_id,
            "website":  website,
            "geometry": {
                "location": {
                    "lat": location.get("lat"),
                    "lng": location.get("lng")
                }
            }
        })

    # next_page_token es simplemente el siguiente offset
    next_offset = str(offset + 1) if len(raw_results) >= 10 else None

    return {
        "results":         results,
        "next_page_token": next_offset,
    }