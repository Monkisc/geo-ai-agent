import requests
import os

from dotenv import load_dotenv

from services.scraper_service import extract_emails_from_website

load_dotenv()

GOOGLE_API_KEY = os.getenv(
    "GOOGLE_MAPS_API_KEY"
)

def search_places(query, page_token=None):

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    params = {
        "query": query,
        "key": GOOGLE_API_KEY
    }

    if page_token:
        params["pagetoken"] = page_token

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    data = response.json()

    print("GOOGLE RESPONSE:")
    print(data)

    results = data.get("results", [])

    next_page_token = data.get(
        "next_page_token"
    )

    final_results = []

    for place in results[:5]:

        try:

            name = place.get("name")

            address = place.get(
                "formatted_address"
            )

            rating = place.get("rating")

            location = (
                place.get("geometry", {})
                .get("location", {})
            )

            lat = location.get("lat")
            lng = location.get("lng")

            website = None
            emails = []

            place_id = place.get("place_id")

            details_url = (
                "https://maps.googleapis.com/maps/api/place/details/json"
            )

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

                blocked_sites = [
                    "facebook.com",
                    "instagram.com",
                    "youtube.com",
                    "wixsite.com",
                    "jimdo"
                ]

                if not any(
                    bad in website
                    for bad in blocked_sites
                ):

                    emails = extract_emails_from_website(
                        website
                    )

            final_results.append({
                "name": name,
                "address": address,
                "rating": rating,
                "lat": lat,
                "lng": lng,
                "website": website,
                "emails": emails
            })

        except Exception as e:

            print("PLACE ERROR:", e)

    return {
        "results": final_results,
        "next_page_token": next_page_token
    }
