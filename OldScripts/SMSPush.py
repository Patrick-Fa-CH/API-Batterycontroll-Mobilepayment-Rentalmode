from __future__ import print_function
import africastalking

shortcode = '21166'
username = "sandbox"   
api_key = "atsk_08de625acf1edae8dade9ab862df2a50f20964eefcff7a1ae5924e646abc08aa81dc99ac"
africastalking.initialize(username, api_key)
sms = africastalking.SMS

def SMSPush(phone_number: str):
    #multiple recipiens possible
    recipients = [f'+{phone_number}']
    message = 'start charging'
    sender = shortcode

    try:
        response = sms.send(message, recipients, sender)
        return response

    except Exception as e:
        print("AfricasTalking SMS sending error:", e)
        return None

