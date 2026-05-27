import requests
from bs4 import BeautifulSoup
import re


def extract_emails(url):

    emails = set()

    possible_pages = [
        "",
        "/contact",
        "/contacto",
        "/about",
        "/nosotros"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for page in possible_pages:

        try:

            full_url = url.rstrip("/") + page

            response = requests.get(
                full_url,
                headers=headers,
                timeout=5
            )

            soup = BeautifulSoup(response.text, "html.parser")

            text = soup.get_text()

            found = re.findall(
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                text
            )

            for email in found:
                emails.add(email)

        except:
            pass

    return list(emails)