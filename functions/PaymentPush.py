### -----------------------------------------------------------------------------### 
### This funtion takes the header with a valid access token as input. ### 
### It creats an API post request to initiate a payment through daraja API. ### 
### The function responses a ResultCode. 0 means the payment initiation went well. ### 
### For online usage, uncomment the CallbackURL ### 
### For online usage, uncomment the url### 
### The function can display the payment informations ### 
### -----------------------------------------------------------------------------### 


from flask import request
import base64
import datetime
import requests
import os

def PaymentPush(head, phone_number, tier, rental_days_left):
    
    MPESA_SHORTCODE = os.environ.get("MPESA_SHORTCODE")
    MPESA_PASSKEY = os.environ.get("MPESA_PASSKEY")
    MPESA_CALLBACK_URL = os.environ.get("MPESA_CALLBACK_URL")
    url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    BYPASS_PHONE_NUMBER_ONE = os.environ.get("BYPASS_PHONE_NUMBER_ONE") #bypass phone number for internal charging. ONLY TRUSTY NUMBER!
    BYPASS_PHONE_NUMBER_TWO = os.environ.get("BYPASS_PHONE_NUMBER_TWO") #bypass phone number for internal charging. ONLY TRUSTY NUMBER!
    BYPASS_PHONE_NUMBER_THREE = os.environ.get("BYPASS_PHONE_NUMBER_THREE") #bypass phone number for internal charging. ONLY TRUSTY NUMBER!

    DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true" 
    if DEMO_MODE == "true":
        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "DEMO123",
                    "CheckoutRequestID": "DEMO_CHECKOUT_001",
                    "ResultCode": 0,
                    "ResultDesc": "Demo payment successful",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 1},
                            {"Name": "MpesaReceiptNumber", "Value": "DEMO123456"},
                            {"Name": "PhoneNumber", "Value": int(phone_number)},
                            {"Name": "TransactionDate", "Value": datetime.datetime.now().strftime("%Y%m%d%H%M%S")}
                        ]
                    }
                }
            }
        }

        try:
            requests.post(MPESA_CALLBACK_URL, json=callback_payload, timeout=5)
        except Exception as e:
            print("Demo callback failed:", e)

        return {
            "ResponseCode": "0",
            "ResponseDescription": "Demo payment simulated",
            "CustomerMessage": "Demo payment successful"
        }
    
    price_map = {
    "20": 100,#58
    "40": 500, #116
    "70": 190, #232
    "80": 500, #232
    "100": 240 #232
    }
    if rental_days_left is not None and rental_days_left > 0:
        Cost = rental_days_left * 1 #290
    else:
        Cost = price_map.get(tier)# only full intiger Cost = XX * 708Wh * 0.028KES/Wh
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    raw = str(MPESA_SHORTCODE) + MPESA_PASSKEY + timestamp    
    password = f"{base64.b64encode(raw.encode()).decode()}"

    if phone_number in {BYPASS_PHONE_NUMBER_ONE, BYPASS_PHONE_NUMBER_TWO, BYPASS_PHONE_NUMBER_THREE}:
        Cost = 1
    
    payload = {
    "Password": password,
    "BusinessShortCode": MPESA_SHORTCODE,
    "Timestamp": timestamp,
    "Amount": int(Cost), 
    "PartyA": f"{phone_number}",
    "PartyB": MPESA_SHORTCODE,
    "TransactionType": "CustomerPayBillOnline",
    "PhoneNumber": f"{phone_number}",
    "TransactionDesc": "Charging",
    "AccountReference": f"C-{phone_number}",
    "CallBackURL": MPESA_CALLBACK_URL #request.host_url.rstrip("/") + "/mpesa/callback"
    }

    response = requests.post(url, json=payload, headers=head)
    #print(f"SMS-Push informations are: {response.json()}")
    return response.json()


