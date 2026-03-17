from flask import request
import requests
import datetime

def PaymentPushB2C(head, Refund, PhoneNumber):
        
    #ResponseURL = request.host_url.rstrip("/") + "/refund/response/wZNHoZNanRgxVowcNDCx"
    TimeOutURL = "https://nonrotational-tatum-readier.ngrok-free.dev/refund/TimeOut/wZNHoZNanRgxVowcNDCx" #for testing
    #CallbackURL = request.host_url.rstrip("/") + "/refund/callback/wZNHoZNanRgxVowcNDCx"
    CallbackURL = "https://nonrotational-tatum-readier.ngrok-free.dev/refund/callback/wZNHoZNanRgxVowcNDCx" #for testing
    #url = "https://api.safaricom.co.ke/mpesa/b2c/v3/paymentrequest"
    url = 'https://sandbox.safaricom.co.ke/mpesa/b2c/v3/paymentrequest' #for testing

    payload = {
    "OriginatorConversationID": "600997_Test_32et3241ed8yu", 
    "InitiatorName": "testapi", 
    "SecurityCredential": "RC6E9WDxXR4b9X2c6z3gp0oC5Th ==", 
    "CommandID": "BusinessPayment", 
    "Amount": f"{Refund}", 
    "PartyA": "600979", 
    "PartyB": '254708374149',# f"{PhoneNumber}", 
    "Remarks": "Thanks for using eWAKA. We are looking forward to serve you again.", 
    "QueueTimeOutURL": TimeOutURL, 
    "ResultURL": CallbackURL, 
    "Occassion":"Refund"  
    }
   
    response = requests.post(url, json=payload, headers=head)
    #print(f"SMS-Push informations are: {response.json()}")
    return response.json()