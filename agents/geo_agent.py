from google import genai
import os
from dotenv import load_dotenv

from services.google_maps_service import search_places

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def ask_agent(user_query, page_token=None):

    places = search_places(user_query, page_token)

    prompt = f"""
    El usuario pidió:

    {user_query}

    Estos son los resultados encontrados:

    {places.get("results", [])[:5]}

    Analiza brevemente los resultados.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "places": places,
        "analysis": response.text
    }
