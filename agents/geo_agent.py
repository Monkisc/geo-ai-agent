from google import genai
import os
from dotenv import load_dotenv
from services.google_maps_service import search_places

# 1. Cargar entorno local si existe el archivo .env
if os.path.exists(".env"):
    load_dotenv()

# 2. Inicializar el cliente de Gemini de forma limpia
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# 3. BLOQUEO MAESTRO: Apagamos Vertex AI para evitar que lea datos corruptos de Cloud Run
if hasattr(client, '_api_client'):
    client._api_client.vertexai = False

def clean_text(text):
    """Fuerza al texto a convertirse a ASCII limpio"""
    if not text:
        return ""
    return str(text).encode('ascii', 'ignore').decode('ascii')

def ask_agent(user_query, page_token=None):
    # Ejecuta la búsqueda de lugares en Maps
    places = search_places(user_query, page_token)

    # Limpieza estricta de textos antes de enviar a Gemini
    clean_query = clean_text(user_query)
    results_list = places.get("results", [])[:5]
    clean_results = clean_text(str(results_list))

    prompt = f"El usuario pidio: {clean_query}. Resultados: {clean_results}. Analiza brevemente."

    # Llamada al modelo
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "places": places,
        "analysis": response.text
    }
