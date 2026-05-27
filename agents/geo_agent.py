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

    prompt = f"""
    El usuario pidió:

    {user_query}

    Estos son los resultados encontrados:

    {places}

    Analiza los resultados y responde de forma organizada y útil.
    """

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        analysis = response.text

    except Exception as e:

        print("GEMINI ERROR:", e)

        analysis = "No fue posible generar el análisis con IA, pero los lugares fueron encontrados correctamente."

    return {
        "places": places,
        "analysis": analysis
    }
