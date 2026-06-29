access_token = None

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
CHASTER_TOKEN_URL = "https://sso.chaster.app/auth/realms/app/protocol/openid-connect/token"


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
        f"&scope=profile locks keyholder"
    )
    return RedirectResponse(url)


@app.get("/callback")
def callback(code: str):
    global access_token

    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    r = requests.post(CHASTER_TOKEN_URL, data=data)
    token_data = r.json()

    access_token = token_data["access_token"]

    return {
        "status": "logged_in",
        "scope": token_data.get("scope"),
    }
    
@app.get("/locks")
def get_locks():
    if not access_token:
        return {"error": "Not logged in"}

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    r = requests.get("https://api.chaster.app/locks", headers=headers)
    return r.json() 
