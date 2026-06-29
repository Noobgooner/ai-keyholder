from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

CHASTER_AUTH_URL = "https://sso.chaster.app/auth/realms/app/protocol/openid-connect/auth"
CHASTER_TOKEN_URL = "https://api.chaster.app/oauth/token"


@app.get("/")
def home():
    return {"status": "AI Keyholder backend running"}


@app.get("/login")
def login():
    url = (
        f"{CHASTER_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=read write"
    )
    return RedirectResponse(url)


@app.get("/callback")
def callback(code: str):
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    r = requests.post(CHASTER_TOKEN_URL, data=data)
    return r.json()
