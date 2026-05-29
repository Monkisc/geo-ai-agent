import requests
import re

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


# ===============================
# EXTRAER EMAILS REALES
# ===============================
def extract_emails_from_website(base_url):

    headers = {

        "User-Agent":
        "Mozilla/5.0"

    }

    emails = set()

    # ===============================
    # PATHS IMPORTANTES
    # ===============================
    paths = [

        "",

        "/contacto",

        "/contact",

        "/admisiones",

        "/about",

        "/nosotros"

    ]

    # ===============================
    # DOMINIO REAL
    # ===============================
    try:

        parsed = urlparse(base_url)

        domain = parsed.netloc.replace("www.", "")

    except:

        domain = ""

    # ===============================
    # SCRAPEAR SOLO PÁGINAS IMPORTANTES
    # ===============================
    for path in paths:

        try:

            url = urljoin(base_url, path)

            response = requests.get(

                url,

                headers=headers,

                timeout=5,

                verify=False

            )

            html = response.text

            soup = BeautifulSoup(html, "html.parser")

            text = soup.get_text()

            found_emails = re.findall(

                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",

                text

            )

            for email in found_emails:

                email = email.lower().strip()

                # ===============================
                # FILTROS BASURA
                # ===============================
                blacklist = [

                    "example",

                    "godaddy",

                    "cpanel",

                    "cloudflare",

                    "wordpress",

                    "wix",

                    "hostinger",

                    "abuse",

                    "webmaster",

                    "test@",

                    "yourdomain",

                    "sentry",

                    "noreply",

                    "no-reply",

                    "alexander@colombiahosting"

                ]

                if any(word in email for word in blacklist):
                    continue

                # evitar strings raros
                if len(email) > 40:
                    continue

                if "?" in email:
                    continue

                if "/" in email:
                    continue

                if "=" in email:
                    continue

                # ===============================
                # VALIDAR DOMINIO
                # ===============================
                if domain:

                    # aceptar gmail SOLO si no hay otra opción
                    if domain not in email and "gmail.com" not in email:
                        continue

                emails.add(email)

        except Exception as e:

            print("SCRAPER ERROR:", e)

            continue

    # ===============================
    # LIMPIAR DUPLICADOS
    # ===============================
    emails = list(emails)

    # ===============================
    # PRIORIZAR DOMINIO PROPIO
    # ===============================
    domain_emails = [

        e for e in emails

        if domain in e

    ]

    gmail_emails = [

        e for e in emails

        if "gmail.com" in e

    ]

    final_emails = domain_emails + gmail_emails

    # máximo 3
    return final_emails[:3]
