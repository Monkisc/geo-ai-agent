import re
import httpx

from bs4 import BeautifulSoup


# ===============================
# VALIDAR EMAIL
# ===============================
def is_valid_email(email):

    blacklist = [

        "example",
        "test",
        "godaddy",
        "cloudflare",
        "wix",
        "sentry",
        "cpanel",
        "apache",
        "hosting",
        "localhost",
        "png",
        "jpg",
        "jpeg",
        "webp",
        ".css",
        ".js",
        "noreply",
        "no-reply"

    ]

    if not email:
        return False

    if len(email) > 45:
        return False

    if "?" in email:
        return False

    if any(word in email.lower() for word in blacklist):
        return False

    return True


# ===============================
# EXTRAER EMAILS
# ===============================
def extract_emails_from_website(url):

    emails = set()

    if not url:
        return []

    headers = {

        "User-Agent":
        "Mozilla/5.0"

    }

    try:

        with httpx.Client(

            follow_redirects=True,

            timeout=5.0,

            headers=headers,

            verify=False

        ) as client:

            response = client.get(url)

            if response.status_code != 200:
                return []

            html = response.text

            soup = BeautifulSoup(

                html,

                "html.parser"

            )

            # ===============================
            # MAILTO
            # ===============================
            for link in soup.find_all("a", href=True):

                href = link["href"]

                if href.startswith("mailto:"):

                    email = href.replace(
                        "mailto:",
                        ""
                    ).split("?")[0].strip().lower()

                    if is_valid_email(email):
                        emails.add(email)

            # ===============================
            # REGEX
            # ===============================
            regex_emails = re.findall(

                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",

                html

            )

            for email in regex_emails:

                email = email.lower().strip()

                if is_valid_email(email):
                    emails.add(email)

            return list(emails)[:5]

    except Exception as e:

        print("SCRAPER ERROR:", e)

        return []
    