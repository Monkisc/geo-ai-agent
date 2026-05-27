# agents/geo_agent.py

from google import genai
import os
from dotenv import load_dotenv

from services.google_maps_service import search_places

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def ask_agent(user_query):

    places = search_places(user_query)

    # LIMITAR TEXTO PARA GEMINI
    places_text = str(places)[:3000]

    prompt = f"""
    El usuario buscó:

    {user_query}

    Estos son algunos resultados encontrados:

    {places_text}

    Resume la información de forma clara,
    útil y organizada.
    """

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        analysis = response.text

    except Exception as e:

        print("GEMINI ERROR:", e)

        analysis = "No fue posible generar el análisis."

    return {
        "places": places,
        "analysis": analysis
    }
