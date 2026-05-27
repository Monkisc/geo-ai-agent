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
        "status": "Geo AI Agent funcionando"
    }

@app.get("/search")
def search(query: str, page_token: str = None):

    result = ask_agent(query, page_token)

    return result

