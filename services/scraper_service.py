import re
import httpx

from bs4 import BeautifulSoup


# ===============================
# BLACKLIST
# ===============================
BLACKLIST = [

    "example",
    "test",
    "godaddy",
    "cloudflare",
    "cpanel",
    "apache",
    "hosting",
    "localhost",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".css",
    ".js",
    "noreply",
    "no-reply",
    "sentry",
    "wix",
    "wordpress",
    "cookie",
    "privacy"

]


# ===============================
# VALIDAR EMAIL
# ===============================
def is_valid_email(email):

    if not email:
        return False

    email = email.lower().strip()

    if "?" in email:
        return False

    if len(email) > 50:
        return False

    if any(word in email for word in BLACKLIST):
        return False

    return True


# ===============================
# EXTRAER EMAILS REALES
# ===============================
def extract_emails_from_website(url):

    if not url:
        return []

    headers = {

        "User-Agent":
        "Mozilla/5.0"

    }

    found_emails = set()

    try:

        with httpx.Client(

            follow_redirects=True,

            timeout=5.0,

            headers=headers,

            verify=False

        ) as client:

            # ===============================
            # HOME
            # ===============================
            response = client.get(url)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(

                response.text,

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
                        found_emails.add(email)

            # ===============================
            # SOLO TEXTO VISIBLE
            # ===============================
            visible_text = soup.get_text(" ")

            regex_emails = re.findall(

                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",

                visible_text

            )

            for email in regex_emails:

                email = email.lower().strip()

                if is_valid_email(email):
                    found_emails.add(email)

            # ===============================
            # FILTRO EXTRA
            # ===============================
            cleaned = []

            for email in found_emails:

                # evitar emails falsos genéricos
                if email.startswith("info@"):

                    domain = email.split("@")[-1]

                    if domain.count(".") < 1:
                        continue

                cleaned.append(email)

            print("EMAILS REALES:", cleaned)

            return cleaned[:5]

    except Exception as e:

        print("SCRAPER ERROR:", e)

        return []
    