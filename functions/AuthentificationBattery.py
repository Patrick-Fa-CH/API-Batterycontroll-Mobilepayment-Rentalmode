import time
import requests
import os

_token = None
_expires = 0

def get_token():
    global _token, _expires
    if _token and time.time() < _expires:
        return _token

    BATTERY_API_BASE_URL = os.environ.get('BATTERY_API_BASE_URL')
    BATTERY_API_USERNAME = os.environ.get('BATTERY_API_USERNAME')
    BATTERY_API_PASSWORD = os.environ.get('BATTERY_API_PASSWORD')
    url = f"{BATTERY_API_BASE_URL}Username={BATTERY_API_USERNAME}&Password={BATTERY_API_PASSWORD}"
    response = requests.request("POST", url, data="")
    response_json = response.json()

    response_block = response_json.get("response") or {}
    token = response_block.get("token")
    expires_in = int(response_block.get("expires_in") or 0)

    if not token:
        raise RuntimeError(f"Token request failed: {response_json}")

    _token = token
    _expires = time.time() + expires_in - 20
    return _token

def AuthHeadBat():
    
    DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"
    if DEMO_MODE:
        return {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer demo-token-battery'
        }
    
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {get_token()}'
    }


