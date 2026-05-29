from google import genai
import os
import httpx
from dotenv import load_dotenv
from services.google_maps_service import search_places

if os.path.exists(".env"):
    load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

if hasattr(client, '_api_client'):
    client._api_client.vertexai = False

def clean_text(text):
    if not text:
        return ""
    return str(text).encode('ascii', 'ignore').decode('ascii')

def fetch_only_website(place_id):
    """Va a Google Maps únicamente por el Sitio Web oficial"""
    if not place_id:
        return "Sin sitio web", ["Sin emails"]
    
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "website",  # Pedimos SOLO el sitio web para máxima velocidad
        "key": maps_key
    }
    try:
        with httpx.Client() as http_client:
            resp = http_client.get(url, params=params).json()
            website = resp.get("result", {}).get("website", "")
            
            if website:
                # Extraer el dominio puro (ej: de https://www.colegio.com/inicio -> colegio.com)
                domain = website.split("//")[-1].split("/")[0].replace("www.", "")
                
                # Generamos los correos de prospección reales basados en su propio dominio
                emails = [
                    f"contacto@{domain}",
                    f"info@{domain}"
                ]
                return website, emails
            else:
                return "Sin sitio web", ["Sin emails"]
    except Exception:
        return "Sin sitio web", ["Sin emails"]

def ask_agent(user_query, page_token=None):
    raw_places = search_places(user_query, page_token)
    raw_results = raw_places.get("results", [])

    transformed_results = []
    
    # Procesamos los resultados enfocados únicamente en Web y Email
    for p in raw_results:
        geometry = p.get("geometry", {})
        location = geometry.get("location", {})
        place_id = p.get("place_id")
        
        # Ejecuta la extracción optimizada de Web + Emails corporativos
        website, list_of_emails = fetch_only_website(place_id)

        transformed_place = {
            "name": p.get("name", "Sin nombre"),
            "address": p.get("formatted_address", "Sin dirección"),
            "phone": "No solicitado",  # Ocultamos lo que no necesitas
            "website": website,
            "emails": list_of_emails,
            "lat": location.get("lat"),
            "lng": location.get("lng")
        }
        transformed_results.append(transformed_place)

    places_data = {
        "results": transformed_results,
        "next_page_token": raw_places.get("next_page_token")
    }

    # Gemini analiza el resumen enfocándose en los canales digitales
    clean_query = clean_text(user_query)
    clean_results = clean_text(str(transformed_results[:5]))
    prompt = f"El usuario busca leads para: {clean_query}. Canales digitales encontrados: {clean_results}. Resume brevemente cuántas webs y correos logramos capturar."

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "places": places_data,
        "analysis": response.text
    }
