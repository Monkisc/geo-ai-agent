from google import genai
import os
from dotenv import load_dotenv
from services.google_maps_service import search_places

if os.path.exists(".env"):
    load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def clean_text(text):
    """Fuerza al texto a convertirse a ASCII limpio para evitar caídas"""
    if not text:
        return ""
    # Convierte caracteres raros o tildes a su versión más cercana en texto plano
    return str(text).encode('ascii', 'ignore').decode('ascii')

def ask_agent(user_query, page_token=None):
    places = search_places(user_query, page_token)

    # Limpiamos el query y los resultados de cualquier tilde oculta
    clean_query = clean_text(user_query)
    results_list = places.get("results", [])[:5]
    clean_results = clean_text(str(results_list))

    prompt = f"El usuario pidio: {clean_query}. Resultados: {clean_results}. Analiza brevemente."

    # Forzamos también a que el modelo use texto plano en inglés/español sin tildes en el envío
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "places": places,
        "analysis": response.text
    }
