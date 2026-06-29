access_token = None

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import os
import requests
from dotenv import load_dotenv
import os
from openai import OpenAI
import json
import re

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

app = FastAPI()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

CHASTER_AUTH_URL = "https://sso.chaster.app/auth/realms/app/protocol/openid-connect/auth"
CHASTER_TOKEN_URL = "https://sso.chaster.app/auth/realms/app/protocol/openid-connect/token"

def extend_lock(lock_id, hours, headers):
    url = f"https://api.chaster.app/locks/{lock_id}/time"

    payload = {
        "operation": "add",
        "hours": hours
    }

    r = requests.post(url, headers=headers, json=payload)
    return r.json()

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
    
@app.get("/ai-decision")
def ai_decision(message: str = ""):
    if not access_token:
        return {"error": "Not logged in"}

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    locks = requests.get(
        "https://api.chaster.app/locks",
        headers=headers
    ).json()

    allowed_actions = ["extend", "send_message"]

    prompt = f"""
You are an AI Keyholder.

Current lock data:
{locks}

User message:
{message}

You may ONLY use one of these actions:
{allowed_actions}

Return ONLY valid JSON in this format:

{{
  "action": "extend",
  "duration_hours": 1,
  "message": "",
  "reason": ""
}}
"""

    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response.choices[0].message.content

    match = re.search(r"\{.*\}", content, re.DOTALL)

    decision = json.loads(match.group())

    lock_id = "6a42bef4a9a72455d86473c8"

    if decision["action"] == "extend":
        result = extend_lock(
            lock_id,
    decision.get("duration_hours", 1),
            headers
        )

        return {
           "ai_decision": decision,
            "chaster_result": result
        }

    return decision
