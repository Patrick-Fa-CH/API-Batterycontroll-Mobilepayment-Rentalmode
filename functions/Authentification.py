### -----------------------------------------------------------------------------### 
### This funtion creates a authentification access token which is needed for all other daraja APIs. ###
### The function return a dictionary with ContentType and AuthorizationBearer. ###
### The first function, get_token() checks if the last token is still valid and only request new tooken if last one is expired.###
### Therefore there are not excessive tokens produced ###
### -----------------------------------------------------------------------------### 

import base64
import time
import requests
import os

_token = None
_expires = 0

def get_token():
    global _token, _expires

    CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
    CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
    credentials = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"

    if _token and time.time() < _expires:
        return _token

    #url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials' #sandbox
    url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    AUTH = {
    "Authorization": f"Basic {base64.b64encode(credentials.encode()).decode()}"
    }

    data = requests.request("GET", url, headers = AUTH, timeout=10).json()
    _token = data["access_token"]
    _expires = time.time() + int(data["expires_in"]) - 20

    return _token

#Request for token
def AuthHead():
    
    DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"
    if DEMO_MODE == "true":
        return {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer demo-token'
        }
    
    return {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {get_token()}'
    }