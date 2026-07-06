import re
import os
import httpx
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ===============================
# CONFIGURACIÓN
# ===============================

if os.path.exists(".env"):
    load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

EMAIL_REGEX = r'\b[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'

BLACKLIST = [
    "noreply", "no-reply", "sentry", "cookie",
    "privacy", "test", "example", "wixpress",
    "sentry.io", "yoursite", "yourdomain",
    "domain.com", "email.com"
]

CONTACT_PATHS = [
    "",
    "/contacto",
    "/contact",
    "/contact-us",
    "/nosotros",
    "/about",
    "/admisiones",
    "/secretaria",
    "/transparencia",
    "/directorio",
    "/administracion",
    "/equipo",
    "/servicios",
    "/atencion",
    "/dependencias",
]


# ===============================
# VALIDACIÓN DE EMAIL
# ===============================

def is_valid_email(email: str) -> bool:
    if not email:
        return False
    email = email.lower().strip()
    if any(email.endswith(ext) for ext in [
        ".png", ".jpg", ".jpeg", ".gif", ".svg",
        ".webp", ".css", ".js", ".ico"
    ]):
        return False
    if any(word in email for word in BLACKLIST):
        return False
    return bool(re.match(EMAIL_REGEX, email))


# ===============================
# OPCIÓN A: GEMINI BUSCA EL EMAIL
# ===============================

def search_emails_with_gemini(place_name: str, website: str) -> list:
    """
    Le pregunta a Gemini directamente cuál es el email de contacto
    de la institución. Usa Search Grounding para buscar en Google.
    """
    try:
        prompt = (
            f"Busca en Google el correo electrónico oficial de contacto de: "
            f"'{place_name}' cuyo sitio web es {website}. "
            f"Responde ÚNICAMENTE con los correos encontrados separados por coma. "
            f"Si no encuentras ninguno responde exactamente: NONE. "
            f"Ejemplo de respuesta válida: info@colegio.edu.co, admisiones@colegio.edu.co"
        )
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        raw = response.text.strip() if response.text else ""

        if not raw or raw.upper() == "NONE":
            return []

        found = re.findall(EMAIL_REGEX, raw)
        valid = [e.lower() for e in found if is_valid_email(e)]
        return valid

    except Exception as e:
        print(f"[search_emails_with_gemini] Error: {e}")
        return []


# ===============================
# OPCIÓN B: PLAYWRIGHT SCRAPING
# ===============================

def extract_emails_from_html(html: str) -> set:
    """Extrae emails válidos del HTML renderizado."""
    emails = set()
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "head"]):
            tag.decompose()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().startswith("mailto:"):
                email = href.replace("mailto:", "").split("?")[0].strip().lower()
                if is_valid_email(email):
                    emails.add(email)

        text = soup.get_text(" ", strip=True)
        for email in re.findall(EMAIL_REGEX, text):
            if is_valid_email(email.lower()):
                emails.add(email.lower())

    except Exception as e:
        print(f"[extract_emails_from_html] Error: {e}")

    return emails


def scrape_with_playwright(website: str) -> list:
    """
    Usa Playwright con Chromium para renderizar JavaScript y extraer
    emails de sitios que bloquean scrapers o cargan contenido dinámico.
    """
    try:
        from playwright.sync_api import sync_playwright

        all_emails = set()
        base_url = website.rstrip("/")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                ignore_https_errors=True,
            )
            page = context.new_page()
            page.set_default_timeout(15000)

            for path in CONTACT_PATHS[:8]:
                try:
                    target_url = base_url + path
                    page.goto(target_url, wait_until="domcontentloaded")
                    page.wait_for_timeout(1500)

                    html = page.content()
                    found = extract_emails_from_html(html)
                    all_emails.update(found)

                    if len(all_emails) >= 3:
                        break

                except Exception as e:
                    print(f"[scrape_with_playwright] {target_url}: {e}")
                    continue

            browser.close()

        return sorted(list(all_emails))[:15]

    except ImportError:
        print("[scrape_with_playwright] Playwright no instalado.")
        return []
    except Exception as e:
        print(f"[scrape_with_playwright] Error general: {e}")
        return []


# ===============================
# OPCIÓN C: GEMINI PRIMERO, PLAYWRIGHT SI FALLA
# ===============================

def _fetch_emails_from_url(client: httpx.Client, url: str) -> set:
    """Scraping estático como último recurso."""
    try:
        response = client.get(url, timeout=7.0)
        if response.status_code == 200:
            return extract_emails_from_html(response.text)
    except Exception as e:
        print(f"[_fetch_emails_from_url] {url}: {e}")
    return set()


def extract_emails_from_website(website: str, place_name: str = "") -> list:
    """
    Estrategia C:
    1. Gemini busca el email directamente en Google  (rapido ~1-2s)
    2. Si no encuentra -> Playwright renderiza el sitio (lento ~4-6s)
    3. Si Playwright falla -> scraping estatico basico  (fallback)
    """
    if not website or website == "Sin sitio web":
        return []

    # PASO 1: Gemini con Search Grounding
    if place_name:
        print(f"[extract_emails] Gemini buscando emails de: {place_name}")
        gemini_emails = search_emails_with_gemini(place_name, website)
        if gemini_emails:
            print(f"[extract_emails] Gemini encontro: {gemini_emails}")
            return gemini_emails
        print(f"[extract_emails] Gemini no encontro, usando Playwright...")

    # PASO 2: Playwright
    #playwright_emails = scrape_with_playwright(website)
    #if playwright_emails:
    #    print(f"[extract_emails] Playwright encontro: {playwright_emails}")
    #    return playwright_emails

   # print(f"[extract_emails] Playwright sin resultados, scraping estatico...")

    # PASO 3: Scraping estático (fallback final)
    base_url = website.rstrip("/")
    all_emails = set()

    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=10.0,
            headers=HEADERS,
            verify=False
        ) as client:
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {
                    executor.submit(
                        _fetch_emails_from_url, client, base_url + path
                    ): path
                    for path in CONTACT_PATHS[:8]
                }
                for future in as_completed(futures):
                    try:
                        all_emails.update(future.result())
                    except Exception:
                        pass
    except Exception as e:
        print(f"[extract_emails] Error scraping estatico: {e}")

    return sorted(list(all_emails))[:15]
