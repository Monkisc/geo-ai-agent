# services/google_maps_service.py

import requests
import re
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GOOGLE_API_KEY = "AIzaSyAsUyVuTHPgQ-8OR8DvYLyGbbxDkkiShP8"


def extract_emails_from_website(url):

    emails_found = []

    try:

        pages_to_try = [
            "",
            "/contacto",
            "/contact",
            "/nosotros",
            "/about",
            "/admisiones"
        ]

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        for page in pages_to_try:

            full_url = url.rstrip("/") + page

            try:

                response = requests.get(
                    full_url,
                    headers=headers,
                    timeout=5,
                    verify=False
                )

                html = response.text

                emails = re.findall(
                    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                    html
                )

                clean_emails = []

                for email in emails:

                    email = email.lower()

                    # FILTROS IMPORTANTES
                    if "error message" in email:
                        continue

                    if "colombiahosting" in email:
                        continue

                    if "?" in email:
                        continue

                    if "example.com" in email:
                        continue

                    clean_emails.append(email)

                emails_found.extend(clean_emails)

            except Exception as e:
                print("SCRAPER ERROR:", full_url, e)
                continue

        return list(set(emails_found))

    except Exception as e:
        print("GENERAL SCRAPER ERROR:", e)
        return []


def search_places(query):

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    params = {
        "query": query,
        "key": GOOGLE_API_KEY
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    data = response.json()

    results = data.get("results", [])

    final_results = []

    # LIMITAR RESULTADOS
    for place in results[:5]:

        name = place.get("name")
        address = place.get("formatted_address")
        rating = place.get("rating")
        location = place.get("geometry", {}).get("location", {})

        lat = location.get("lat")
        lng = location.get("lng")

        website = None
        emails = []

        try:

            place_id = place.get("place_id")

            details_url = "https://maps.googleapis.com/maps/api/place/details/json"

            details_params = {
                "place_id": place_id,
                "fields": "website",
                "key": GOOGLE_API_KEY
            }

            details_response = requests.get(
                details_url,
                params=details_params,
                timeout=5
            )

            details_data = details_response.json()

            website = (
                details_data
                .get("result", {})
                .get("website")
            )

            if website:

                # FILTRO SITIOS MALOS
                bad_sites = [
                    "facebook.com",
                    "instagram.com",
                    "wixsite.com",
                    "jimdo",
                    "youtube.com"
                ]

                if any(site in website for site in bad_sites):
                    website = None

                else:

                    print("==========================")
                    print("WEB:", website)

                    emails = extract_emails_from_website(
                        website
                    )

                    print("EMAILS ENCONTRADOS:", emails)

        except Exception as e:
            print("DETAILS ERROR:", e)

        final_results.append({
            "name": name,
            "address": address,
            "rating": rating,
            "lat": lat,
            "lng": lng,
            "website": website,
            "emails": emails
        })

    return {
        "results": final_results
    }
