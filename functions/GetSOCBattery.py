import json
import requests
import os

def get_battery_soc(header: dict, battery_number: str,  timeout: int = 15):
    
    DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"
    if DEMO_MODE == "true":
        print("-----DEMO: SOC of 50 returned-----", battery_number)
        return 50 
    
    ptid: int = 6
    bms_type: int = 227
    url = f"https://dev.iov18.com/api/Monitor/ShowRealtimeBMSData?Code={battery_number}&type={bms_type}&ptid={ptid}"

    response = requests.post(url, headers=header, timeout=timeout)
    #successful response format: {"status":200,"success":true,"msg":"Get Success","msgDev":null,"response":{"Code":"058215000290",
    # "BmsType":227,"PTid":6,"ReceiveTime":"2,022-02-25 18:21:01","JsonData":"{\"BatteryVoltages\":[{\"N....
    # .......ull,"ChargeMOS":null,"CreateTime":"2022-02-18 11:09:26","LastUpdateTime":"2022-02-25 18:21:01","Id":24}}

    response.raise_for_status() #check if http request was successful, no error code
    data = response.json()

    resp = data.get("response") or {}
    json_str = resp.get("JsonData")
    if not json_str:
        return None  #  No data available at all

    try:
        bms = json.loads(json_str) #convert json string to dict
        SOC = bms.get("SOC")
        return int(SOC) if SOC is not None else None
    
    except Exception:
        return None