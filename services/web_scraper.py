import re
import requests

from bs4 import BeautifulSoup


EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def clean_email(email):

    email = email.strip().lower()

    email = email.replace("mailto:", "")

    return email


def extract_emails_from_text(text):

    emails = re.findall(EMAIL_REGEX, text)

    cleaned = []

    for email in emails:

        email = clean_email(email)

        if email not in cleaned:
            cleaned.append(email)

    return cleaned


def try_page(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=6,
            verify=False
        )

        html = response.text

        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text(" ")

        emails = extract_emails_from_text(text)

        # También revisar links mailto
        for a in soup.find_all("a", href=True):

            href = a["href"]

            if "mailto:" in href:

                email = clean_email(href)

                if email not in emails:
                    emails.append(email)

        return emails

    except Exception as e:

        print("SCRAPER ERROR:", url, e)

        return []


def extract_contact_info(website):

    emails = []

    possible_pages = [
        "",
        "/contacto",
        "/contact",
        "/nosotros",
        "/about",
        "/admisiones",
        "/transparencia"
    ]

    for page in possible_pages:

        try:

            url = website.rstrip("/") + page

            found = try_page(url)

            for email in found:

                if email not in emails:
                    emails.append(email)

            # SI YA ENCONTRÓ CORREOS
            # NO SIGUE PERDIENDO TIEMPO
            if len(emails) >= 2:
                break

        except:
            pass

    return {
        "emails": emails
    }
