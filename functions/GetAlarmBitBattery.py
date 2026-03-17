import json
import requests
import os

def get_battery_alarm_bits(header: dict, battery_number: str, timeout: int = 15):
    
    DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"
    if DEMO_MODE:
        print("-----DEMO: BMSAlarm 0 returned-----", battery_number)
        return 0
    
    ptid: int = 6
    bms_type: int = 227
    url = f"https://dev.iov18.com/api/Monitor/ShowRealtimeBMSData?Code={battery_number}&type={bms_type}&ptid={ptid}"

    response = requests.post(url, headers=header, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    resp = data.get("response") or {}
    json_str = resp.get("JsonData")
    if not json_str:
        return None

    try:
        bms = json.loads(json_str)
        bms_alarm = bms.get("BMSAlarm")
        return int(bms_alarm) if bms_alarm is not None else None
    except Exception:
        return None