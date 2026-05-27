import os
import time
import googlemaps

from dotenv import load_dotenv

from services.web_scraper import extract_contact_info

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

gmaps = googlemaps.Client(key=API_KEY)


def search_places(query):

    all_places = []

    try:

        response = gmaps.places(query=query)

        results = response.get("results", [])

        all_places.extend(results)

        while "next_page_token" in response:

            time.sleep(2)

            response = gmaps.places(
                query=query,
                page_token=response["next_page_token"]
            )

            results = response.get("results", [])

            all_places.extend(results)

    except Exception as e:

        print("ERROR EN BÚSQUEDA:", e)

    final_results = []

    for place in all_places:

        try:

            place_id = place.get("place_id")

            details = gmaps.place(
                place_id=place_id,
                fields=[
                    "name",
                    "formatted_address",
                    "website",
                    "formatted_phone_number",
                    "international_phone_number",
                    "rating",
                    "geometry"
                ]
            )

            result = details.get("result", {})

            geometry = result.get("geometry", {})
            location = geometry.get("location", {})

            website = result.get("website")

            emails = []

            # EXTRAER EMAILS
            if website:

                print("\n==========================")
                print("WEB:", website)

                contact = extract_contact_info(website)

                emails = contact.get("emails", [])

                print("EMAILS ENCONTRADOS:", emails)

            # TELÉFONOS GOOGLE
            phones = []

            google_phone = result.get("formatted_phone_number")

            intl_phone = result.get("international_phone_number")

            if google_phone:
                phones.append(google_phone)

            if intl_phone and intl_phone not in phones:
                phones.append(intl_phone)

            final_results.append({

                "name": result.get("name"),

                "address": result.get("formatted_address"),

                "website": website,

                "rating": result.get("rating"),

                "phones": phones,

                "emails": emails,

                "lat": location.get("lat"),

                "lng": location.get("lng")
            })

        except Exception as e:

            print("ERROR EN DETAILS:", e)

    return {
        "results": final_results
    }

