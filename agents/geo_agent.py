from google import genai
from google.genai import types
import os
import re
import httpx
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.google_maps_service import search_places
from services.scraper_service import extract_emails_from_website

if os.path.exists(".env"):
    load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
if hasattr(client, "_api_client"):
    client._api_client.vertexai = False

MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()


def clean_text(text):
    if not text:
        return ""
    return str(text).encode("ascii", "ignore").decode("ascii")


def search_official_website_on_google(place_name: str) -> str | None:
    try:
        prompt = (
            f"Busca en Google el sitio web oficial de: '{place_name}'. "
            f"Responde ÚNICAMENTE con la URL principal, sin texto adicional. "
            f"Ejemplo: https://colegio.edu.co"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        raw = response.text.strip() if response.text else ""
        urls = re.findall(r'https?://[^\s<>"\')\]]+', raw)
        excluded = ["google.com", "googleapis.com", "gstatic.com", "gemini"]
        for url in urls:
            if not any(ex in url for ex in excluded):
                return url.rstrip("/.,)")
    except Exception as e:
        print(f"[search_official_website_on_google] Error: {e}")
    return None


def enrich_one(place: dict) -> dict:
    """Enriquece un lugar con website y emails."""
    place_name = place.get("name", "Sin nombre")
    website    = place.get("website", "")

    if not website:
        website = search_official_website_on_google(place_name) or ""

    emails = []
    if website:
        emails = extract_emails_from_website(website, place_name)

    return {
        **place,
        "website": website or "Sin sitio web",
        "emails":  emails if emails else ["Sin emails"],
    }


def enrich_places(places: list) -> list:
    """Enriquece una lista de lugares con emails en paralelo."""
    results = [None] * len(places)
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_index = {
            executor.submit(enrich_one, places[i]): i
            for i in range(len(places))
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                print(f"[enrich_places] Error en lugar {idx}: {e}")
                results[idx] = {
                    **places[idx],
                    "website": "Sin sitio web",
                    "emails":  ["Sin emails"],
                }
    return [r for r in results if r is not None]


def ask_agent(user_query: str, page_token: str = None) -> dict:
    """
    Devuelve lugares SIN emails (rápido).
    El next_page_token se devuelve fresco al frontend.
    """
    raw_places  = search_places(user_query, page_token)
    raw_results = raw_places.get("results", [])
    next_token  = raw_places.get("next_page_token")

    print(f"[ask_agent] {len(raw_results)} lugares | token: {'Si' if next_token else 'No'}")

    # Devolver lugares sin emails — el frontend los enriquece luego
    places = []
    for p in raw_results:
        geometry = p.get("geometry", {})
        location = geometry.get("location", {})
        places.append({
            "name":     p.get("name", "Sin nombre"),
            "place_id": p.get("place_id", ""),
            "website":  p.get("website", ""),
            "emails":   [],
            "lat":      location.get("lat"),
            "lng":      location.get("lng"),
        })

    return {
        "places": {
            "results":         places,
            "next_page_token": next_token,
        },
        "analysis": "",
    }
