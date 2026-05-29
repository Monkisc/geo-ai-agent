import os
import httpx
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()

def clean_text(text):
    """Limpia cualquier formato o tilde oculta de los textos y llaves"""
    if not text:
        return ""
    return str(text).encode('ascii', 'ignore').decode('ascii')

def search_places(query, page_token=None):
    # 1. Limpiamos la API Key de Maps de cualquier tilde o espacio invisible (\xcd)
    raw_api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    api_key = clean_text(raw_api_key).strip()

    # 2. Limpiamos la consulta del usuario
    clean_query = clean_text(query)

    # Construimos la URL oficial de Google Places API
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    params = {
        "query": clean_query,
        "key": api_key
    }
    
    if page_token:
        params["pagetoken"] = page_token

    # Hacemos la petición de forma segura
    try:
        response = httpx.get(url, params=params)
        return response.json()
    except Exception as e:
        return {"error": f"Error al conectar con Google Maps: {str(e)}", "results": []}
    