from google import genai
import os

from dotenv import load_dotenv

from services.google_maps_service import search_places


# ===============================
# LOAD ENV
# ===============================
if os.path.exists(".env"):
    load_dotenv()


# ===============================
# GEMINI
# ===============================
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ===============================
# CLEAN TEXT
# ===============================
def clean_text(text):

    if not text:
        return ""

    return str(text).encode(
        "ascii",
        "ignore"
    ).decode("ascii")


# ===============================
# ASK AGENT
# ===============================
def ask_agent(user_query, page_token=None):

    places_data = search_places(
        user_query,
        page_token
    )

    transformed_results = places_data.get(
        "results",
        []
    )

    clean_query = clean_text(user_query)

    prompt = f"""

    El usuario busca:

    {clean_query}

    Analiza los resultados encontrados.

    """

    try:

        response = client.models.generate_content(

            model="gemini-2.5-flash",

            contents=prompt

        )

        analysis = response.text

    except Exception as e:

        print("GEMINI ERROR:", e)

        analysis = "No se pudo generar análisis IA."

    return {

        "places": {

            "results": transformed_results,

            "next_page_token":
            places_data.get("next_page_token")

        },

        "analysis": analysis

    }
