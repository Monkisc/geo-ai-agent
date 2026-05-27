import requests
import re

from bs4 import BeautifulSoup

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

def extract_emails_from_website(url):

    emails = set()

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=5,
            verify=False
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        text = soup.get_text()

        found = re.findall(
            EMAIL_REGEX,
            text
        )

        for email in found:

            if "?" not in email:
                emails.add(email)

    except Exception as e:

        print("SCRAPER ERROR:", e)

    return list(emails)[:3]
