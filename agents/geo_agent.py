from google import genai
from google.genai import types
import os
import httpx
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from services.google_maps_service import search_places

if os.path.exists(".env"):
    load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

if hasattr(client, '_api_client'):
    client._api_client.vertexai = False

def clean_text(text):
    if not text:
        return ""
    return str(text).encode('ascii', 'ignore').decode('ascii')

def search_official_website_on_google(place_name):
    """Busca en Google internet la URL oficial exacta mediante Search Grounding"""
    try:
        prompt = (
            f"Busca en Google internet el sitio web oficial de la institución: '{place_name} Colombia'. "
            f"Extrae la URL principal y responde ÚNICAMENTE con esa URL (ejemplo: https://glm.edu.co). "
            f"No agregues explicaciones, ni introducciones, solo la URL limpia."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        predicted_url = response.text.strip()
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', predicted_url)
        if urls:
            return urls[0].rstrip('/')
    except Exception as e:
        print(f"Error en Google Search: {str(e)}")
    return None

def extract_emails_from_html(html_content):
    """Busca cadenas con estructura de email dentro de un bloque HTML"""
    soup = BeautifulSoup(html_content, "html.parser")
    page_text = soup.get_text()
    email_pattern = r'[a-zA-Z0-9-_\.]+@[a-zA-Z0-9-_\.]+\.[a-zA-Z]{2,5}'
    found_emails = re.findall(email_pattern, page_text)
    
    clean_emails = []
    for email in found_emails:
        email_lower = email.lower()
        if not any(email_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']):
            if email not in clean_emails:
                clean_emails.append(email)
    return clean_emails

def scrape_emails_deep(website_url):
    """Visita la URL y extrae correos de la Home o subpáginas de contacto"""
    if not website_url or website_url == "Sin sitio web":
        return ["Sin emails"]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        with httpx.Client(follow_redirects=True, timeout=6.0, headers=headers) as http_client:
            response = http_client.get(website_url)
            if response.status_code == 200:
                emails = extract_emails_from_html(response.text)
                if emails:
                    return emails
                
                soup = BeautifulSoup(response.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    href = link["href"].lower()
                    if "contact" in href or "contacto" in href or "contactenos" in href:
                        subpage_url = href if href.startswith("http") else f"{website_url.rstrip('/')}/{href.lstrip('/')}"
                        try:
                            sub_resp = http_client.get(subpage_url, timeout=4.0)
                            if sub_resp.status_code == 200:
                                sub_emails = extract_emails_from_html(sub_resp.text)
                                if sub_emails:
                                    return sub_emails
                        except Exception:
                            continue
            return ["No se encontraron emails en el sitio"]
    except Exception:
        return ["No se pudo escanear el sitio"]

def fetch_leads_data(place_id, place_name):
    """Obtiene el sitio web de Maps o Google Search y gatilla el scraper"""
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "website",
        "key": maps_key
    }
    
    website = "Sin sitio web"
    try:
        if place_id:
            with httpx.Client() as http_client:
                resp = http_client.get(url, params=params).json()
                website = resp.get("result", {}).get("website", "")
    except Exception:
        pass
        
    if not website or website == "Sin sitio web":
        real_google_url = search_official_website_on_google(place_name)
        if real_google_url:
            website = real_google_url

    if website and website != "Sin sitio web":
        real_emails = scrape_emails_deep(website)
        return website, real_emails
    
    return "Sin sitio web", ["Sin emails"]

def ask_agent(user_query, page_token=None):
    # Traemos la respuesta de tu servicio de mapas
    raw_places = search_places(user_query, page_token)
    raw_results = raw_places.get("results", [])

    transformed_results = []
    
    # FORZADO DE CONTROL: Nos aseguramos de leer hasta 10 elementos de la lista
    limit = min(25, len(raw_results))
    print(f"Procesando un total de {limit} lugares para el frontend.")

    for i in range(limit):
        p = raw_results[i]
        geometry = p.get("geometry", {})
        location = geometry.get("location", {})
        
        lat_val = location.get("lat")
        lng_val = location.get("lng")
        place_id = p.get("place_id")
        place_name = p.get("name", "Sin nombre")
        
        website, real_emails_list = fetch_leads_data(place_id, place_name)

        transformed_place = {
            "name": place_name,
            "address": "No solicitada", 
            "phone": "No solicitado",     
            "website": website,
            "emails": real_emails_list,
            "lat": lat_val,
            "lng": lng_val
        }
        transformed_results.append(transformed_place)

    places_data = {
        "results": transformed_results,
        "next_page_token": raw_places.get("next_page_token")
    }

    clean_query = clean_text(user_query)
    clean_results = clean_text(str(transformed_results))
    prompt = f"El usuario busca leads para: {clean_query}. Muestra: {clean_results}."

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "places": places_data,
        "analysis": response.text
    }
