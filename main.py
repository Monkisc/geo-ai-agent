import sys
import os

print("--- INICIANDO CAPTURA DE ARRANQUE ---")

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    # Aquí es donde sospecho que se está rompiendo (en las importaciones)
    print("Cargando agentes y servicios...")
    from agents.geo_agent import ask_agent
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

    @app.get("/search")
    def search(query: str, page_token: str = None):
        result = ask_agent(query, page_token)
        return result

except Exception as e:
    print("\n" + "="*50)
    print("¡CRASHEO EN EL ARRANQUE DEL BACKEND!")
    print(f"ERROR EXACTO: {e}")
    import traceback
    traceback.print_exc()
    print("="*50 + "\n")
    # Forzamos una salida limpia pero dejamos el log escrito
    sys.exit(1)
    