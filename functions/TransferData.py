from datetime import timezone
from zoneinfo import ZoneInfo
import requests
from models.ChargersBatterys import Battery, charger
import os

def time_to_nairobi_string(dt):
    if dt is None:
        return None
    
    if dt.tzinfo is None: #fallback if time naive
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(ZoneInfo("Africa/Nairobi")).strftime("%Y-%m-%d %H:%M:%S")

def send_charger_details(charger_number):
    
    charger_get = charger.query.get(charger_number)
    if charger_get is None:
        return None
    charger_body = {
        'charger_number' : charger_get.charger_number, # four digit charger number
        'phone_number' : charger_get.phone_number, # 2547xxxxxxxx
        'tier' : charger_get.tier, #20|40|80
        'payment_status' : charger_get.payment_status, # waiting|success|failed
        'charging_status' : charger_get.charging_status, # prohibited|granted
        'checkout_request_id' : charger_get.checkout_request_id,
        "updated_at": time_to_nairobi_string(charger_get.updated_at)   if charger_get.updated_at else None
    }
    try:
        THIRD_PARTY_IOT_URL_CHARGER = os.environ.get("THIRD_PARTY_IOT_URL_CHARGER")
        r = requests.post(THIRD_PARTY_IOT_URL_CHARGER, json=charger_body, timeout=4)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("send_charger_details failed:", e)
        return None
    
def send_battery_details(battery_number):

    battery_get = Battery.query.get(battery_number)
    if battery_get is None:
        return None
    battery_body = {
        'phone_number' : battery_get.phone_number, # 2547xxxxxxxx
        'battery_number' : battery_get.battery_number, # 12-digit battery number
        'payment_status' : battery_get.payment_status, # waiting|success|failed
        'tier' : battery_get.tier, #20|40|80
        'rental_days_left' : battery_get.rental_days_left, # number of rental days left, only relevant if battery is rented
        'day_expires_at' : time_to_nairobi_string(battery_get.day_expires_at)    if battery_get.day_expires_at else None, # expiration date of rental period, only relevant if battery is rented
        'charging_status' : battery_get.charging_status, # prohibited|granted|loading|charging disable fail
        'discharging_status' : battery_get.discharging_status, # prohibited|granted|discharging disable fail
        'SOC' : battery_get.SOC, # 0-100
        'used_credit' : battery_get.used_credit, # 0-80
        'number_of_sessions' : battery_get.number_of_sessions, # number of sessions
        'number_of_cycles' : battery_get.number_of_cycles, # number of cycles
        'checkout_request_id' : battery_get.checkout_request_id,
        'last_payment_at' : time_to_nairobi_string(battery_get.last_payment_at)    if battery_get.last_payment_at else None,
        "updated_at": time_to_nairobi_string(battery_get.updated_at)    if battery_get.updated_at else None
        }
    try:
        THIRD_PARTY_IOT_URL_BATTERY = os.environ.get("THIRD_PARTY_IOT_URL_BATTERY")
        r = requests.post(THIRD_PARTY_IOT_URL_BATTERY, json=battery_body, timeout=4)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("send_battery_details failed:", e)
        return None