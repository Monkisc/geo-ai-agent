from google import genai
import os
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

def ask_agent(user_query, page_token=None):
    # 1. Obtener la respuesta cruda de Google Maps
    raw_places = search_places(user_query, page_token)
    raw_results = raw_places.get("results", [])

    transformed_results = []
    
    # 2. TRANSFORMACIÓN: Estructuramos los datos tal cual los espera tu JavaScript
    for p in raw_results:
        # Extraer coordenadas de forma segura
        geometry = p.get("geometry", {})
        location = geometry.get("location", {})
        
        transformed_place = {
            "name": p.get("name", "Sin nombre"),
            "address": p.get("formatted_address", p.get("vicinity", "Sin dirección")),
            "phone": p.get("international_phone_number", p.get("formatted_phone_number", "Sin teléfono")),
            "website": p.get("website", "Sin sitio web"),
            "emails": p.get("emails", []),
            "lat": location.get("lat"),
            "lng": location.get("lng")
        }
        transformed_results.append(transformed_place)

    # Reconstruimos la estructura para que data.places.results funcione en tu JS
    places_data = {
        "results": transformed_results,
        "next_page_token": raw_places.get("next_page_token")
    }

    # 3. Preparar prompt para Gemini
    clean_query = clean_text(user_query)
    clean_results = clean_text(str(transformed_results[:5]))
    prompt = f"El usuario pidio: {clean_query}. Resultados: {clean_results}. Analiza brevemente."

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "places": places_data,
        "analysis": response.text
    }
