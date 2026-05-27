# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.geo_agent import ask_agent

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

    return {
        "status": "API funcionando correctamente"
    }


@app.get("/search")
def search(query: str):

    try:

        result = ask_agent(query)

        return result

    except Exception as e:

        print("SEARCH ERROR:", e)

        return {
            "error": str(e)
        }
    