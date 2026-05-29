from google import genai
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

def scrape_emails_from_website(website_url):
    """Visita el sitio web real y extrae los correos electrónicos publicados utilizando Regex"""
    if not website_url or website_url == "Sin sitio web":
        return ["Sin emails"]
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # Hacemos la petición a la web con un timeout corto de 4 segundos para que no ralentice la app
        with httpx.Client(follow_redirects=True, timeout=4.0, headers=headers) as http_client:
            response = http_client.get(website_url)
            if response.status_code != 200:
                return ["No se pudo acceder al sitio"]
            
            # Usamos BeautifulSoup para procesar el texto HTML de la página
            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text()
            
            # Expresión regular para capturar estructuras de correos electrónicos válidos
            email_pattern = r'[a-zA-Z0-9-_\.]+@[a-zA-Z0-9-_\.]+\.[a-zA-Z]{2,5}'
            found_emails = re.findall(email_pattern, page_text)
            
            # Limpiamos duplicados y filtramos extensiones de archivos comunes que confunden al regex (.png, .jpg)
            clean_emails = []
            for email in found_emails:
                email_lower = email.lower()
                if not any(email_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']):
                    if email not in clean_emails:
                        clean_emails.append(email)
            
            if clean_emails:
                return clean_emails
            else:
                return ["No se encontraron emails en el sitio"]
                
    except Exception as e:
        print(f"Error raspando la web {website_url}: {str(e)}")
        return ["No se pudo escanear el sitio"]

def fetch_only_website_and_real_emails(place_id):
    """Obtiene el sitio web de Google Maps y gatilla el scraper para extraer los correos verdaderos"""
    if not place_id:
        return "Sin sitio web", ["Sin emails"]
    
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "website",
        "key": maps_key
    }
    
    try:
        with httpx.Client() as http_client:
            resp = http_client.get(url, params=params).json()
            website = resp.get("result", {}).get("website", "")
            
            if website:
                # ¡Aquí ocurre la magia! Vamos a raspar la web real encontrada
                real_emails = scrape_emails_from_website(website)
                return website, real_emails
            else:
                return "Sin sitio web", ["Sin emails"]
    except Exception:
        return "Sin sitio web", ["Sin emails"]

def ask_agent(user_query, page_token=None):
    raw_places = search_places(user_query, page_token)
    raw_results = raw_places.get("results", [])

    transformed_results = []
    
    # Procesamos los primeros 5 resultados para mantener un tiempo de respuesta óptimo en la web
    for p in raw_results[:5]:
        geometry = p.get("geometry", {})
        location = geometry.get("location", {})
        place_id = p.get("place_id")
        
        # Obtener el sitio web real de Google Maps y raspar sus correos reales
        website, real_emails_list = fetch_only_website_and_real_emails(place_id)

        transformed_place = {
            "name": p.get("name", "Sin nombre"),
            "address": "No solicitada",   # Limpiamos lo que no necesitas ver en tu UI
            "phone": "No solicitado",     # Limpiamos lo que no necesitas ver en tu UI
            "website": website,
            "emails": real_emails_list,
            "lat": location.get("lat"),
            "lng": location.get("lng")
        }
        transformed_results.append(transformed_place)

    places_data = {
        "results": transformed_results,
        "next_page_token": raw_places.get("next_page_token")
    }

    # Redactamos el prompt para Gemini enfocado 100% en el análisis comercial/leads reales
    clean_query = clean_text(user_query)
    clean_results = clean_text(str(transformed_results))
    prompt = (
        f"El usuario busca leads reales para: {clean_query}. "
        f"Sitios webs y correos REALES extraídos del HTML: {clean_results}. "
        f"Analiza la efectividad de la recolección de canales digitales."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "places": places_data,
        "analysis": response.text
    }
