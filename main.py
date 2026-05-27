from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.geo_agent import ask_agent

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():

    return {
        "status": "ok",
        "message": "Geo AI Agent funcionando 🚀"
    }

@app.get("/search")
def search(query: str):

    result = ask_agent(query)

    return result
