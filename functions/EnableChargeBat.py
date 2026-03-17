# -----------------------------------------------------------------------------
# This function sends FM-MOS OFF command.
# If command delivery fails, it retries up to max_retries
# or stops after max_total_time seconds.
# -----------------------------------------------------------------------------

import requests
import time
import os

def set_fm_mos_charging_on(header,battery_number: str):

    DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"
    if DEMO_MODE == "true":
        print("-----DEMO: Battery charging activated through API-----", battery_number)
        return True 

    BATTERY_API_COMMAND_URL = os.environ.get('BATTERY_API_COMMAND_URL')

    body = {
        "cmdKey": "8900_F030",
        "data": {
            "CmdKey": "8900_F030",
            "Code": battery_number,
            "Parameter": "1"
        }
    }
    max_retries: int = 4
    retry_delay: int = 3
    max_total_time: int = 20
    start_time = time.time()
    attempt = 0

    while attempt < max_retries and (time.time() - start_time) < max_total_time:
        attempt += 1

        try:
            response = requests.post(BATTERY_API_COMMAND_URL, headers=header, json=body,timeout=15)
            response.raise_for_status() #check if request was successful, no error code
            data = response.json()

            if data.get("response") is True:
                print("-----Battery charge activated through API-----", battery_number)
                return True

            else:
                print("----API response indicates failure, retrying...----", data)

        except Exception as e:
            print("Request error:", e)
        time.sleep(retry_delay)

    print("\n-----Failed to get answer from API in time-----")
    return False