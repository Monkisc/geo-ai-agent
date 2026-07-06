import sys
import os

print("--- INICIANDO CAPTURA DE ARRANQUE ---")

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List

    print("Cargando agentes y servicios...")
    from agents.geo_agent import ask_agent, enrich_places
    print("¡Módulos cargados con éxito!")

    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root():
        return {"status": "ok"}

    # Endpoint 1: Búsqueda rápida, sin emails
    @app.get("/search")
    def search(query: str, page_token: str = None):
        result = ask_agent(query, page_token)
        return result

    # Endpoint 2: Enriquecer con emails
    class EnrichRequest(BaseModel):
        places: List[dict]

    @app.post("/enrich")
    def enrich(body: EnrichRequest):
        enriched = enrich_places(body.places)
        return {"places": enriched}

except Exception as e:
    print("\n" + "="*50)
    print("¡CRASHEO EN EL ARRANQUE DEL BACKEND!")
    print(f"ERROR EXACTO: {e}")
    import traceback
    traceback.print_exc()
    print("="*50 + "\n")
    sys.exit(1)

    