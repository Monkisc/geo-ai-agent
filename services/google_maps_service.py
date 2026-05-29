import os
import httpx

from dotenv import load_dotenv

from services.scraper_service import extract_emails_from_website


# ===============================
# LOAD ENV
# ===============================
if os.path.exists(".env"):
    load_dotenv()


# ===============================
# LIMPIAR TEXTO
# ===============================
def clean_text(text):

    if not text:
        return ""

    return str(text).encode(
        "ascii",
        "ignore"
    ).decode("ascii")


# ===============================
# BUSCAR LUGARES
# ===============================
def search_places(query, page_token=None):

    raw_api_key = os.getenv(
        "GOOGLE_MAPS_API_KEY",
        ""
    )

    api_key = clean_text(
        raw_api_key
    ).strip()

    clean_query = clean_text(query)

    # ===============================
    # URL TEXT SEARCH
    # ===============================
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    params = {

        "query": clean_query,

        "key": api_key

    }

    # PAGINACIÓN
    if page_token:
        params["pagetoken"] = page_token

    try:

        response = httpx.get(

            url,

            params=params,

            timeout=20

        )

        data = response.json()

        results = []

        # ===============================
        # RECORRER RESULTADOS
        # ===============================
        for place in data.get("results", []):

            place_id = place.get("place_id")

            details = get_place_details(
                place_id,
                api_key
            )

            website = details.get(
                "website",
                ""
            )

            phone = details.get(
                "formatted_phone_number",
                "No disponible"
            )

            # ===============================
            # EXTRAER EMAILS
            # ===============================
            emails = []

            if website:

                emails = extract_emails_from_website(
                    website
                )

            # ===============================
            # RESULTADO FINAL
            # ===============================
            results.append({

                "name":
                place.get("name", "Sin nombre"),

                "address":
                place.get(
                    "formatted_address",
                    "Sin dirección"
                ),

                "location": {

                    "lat":
                    place["geometry"]["location"]["lat"],

                    "lng":
                    place["geometry"]["location"]["lng"]

                },

                "website":
                website,

                "phone":
                phone,

                "emails":
                emails

            })

        # ===============================
        # RETORNAR
        # ===============================
        return {

            "results": results,

            "next_page_token":
            data.get("next_page_token")

        }

    except Exception as e:

        print("GOOGLE MAPS ERROR:", e)

        return {

            "results": [],

            "error": str(e)

        }


# ===============================
# PLACE DETAILS
# ===============================
def get_place_details(place_id, api_key):

    try:

        url = "https://maps.googleapis.com/maps/api/place/details/json"

        params = {

            "place_id": place_id,

            "fields":
            "website,formatted_phone_number",

            "key": api_key

        }

        response = httpx.get(

            url,

            params=params,

            timeout=15

        )

        data = response.json()

        return data.get(
            "result",
            {}
        )

    except Exception as e:

        print("DETAILS ERROR:", e)

        return {}
    