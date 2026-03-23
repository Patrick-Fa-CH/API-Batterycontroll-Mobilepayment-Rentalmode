### This script continuously monitors the SOC of batteries that have an active SOC_limit set. 
### If a battery's SOC reaches or exceeds its limit, the script will disable charging 
### for that battery and reset the SOC_limit to prevent further charging until manually re-enabled. 
### The script runs indefinitely and should be run direct on VPS, polling every 2 minutes.

import time
from datetime import datetime, timedelta
from main import app, db, Battery

from functions.AuthentificationBattery import AuthHeadBat
from functions.GetSOCBattery import get_battery_soc
from functions.DisableChargeBat import set_fm_mos_charging_off
from functions.EnableChargeBat import set_fm_mos_charging_on 
from functions.DisableDischargeBat import set_fm_mos_discharging_off
from functions.EnableDischargeBat import set_fm_mos_discharging_on
from functions.TransferData import send_battery_details, send_charger_details
POLL_SECONDS = 120  # 2 minutes
RENTAL_DAILY_LIMIT = 240 # maximum SOC charge per day


def run():
    print("-----SOC_Watcher started-----")

    while True:
        try:
            with app.app_context():
                batteries = Battery.query.filter(Battery.charging_status.in_(["granted", "failed"])).all()

                if not batteries:
                    time.sleep(POLL_SECONDS)
                    continue

                header = AuthHeadBat()
                for b in batteries:
                    try: 
                        soc = get_battery_soc(header, b.battery_number)
                        if soc is None:     # If API returns no SOC, skip this battery for now
                            b.updated_at = datetime.utcnow()
                            db.session.add(b)
                            db.session.commit()
                            send_battery_details(b.battery_number) # Send update to dashboard
                            continue
                        ChargedAmount = int(soc) - int(b.SOC) if b.SOC is not None else 0 # Calculate how much SOC has been charged since last check
                        if ChargedAmount < 0: # If SOC decreased, it means battery was used
                            ChargedAmount = 0 # In this case, we don't want to count negative charging, so we set it to 0
                        b.used_credit = int(b.used_credit or 0) + ChargedAmount # Update used credit
                        b.SOC = int(soc)                     # Store the latest SOC in DB
                        b.number_of_cycles = (b.number_of_cycles or 0.0) + (ChargedAmount / 100.0)
                        b.updated_at = datetime.utcnow()
                        db.session.add(b)
                        db.session.commit()

                        if b.rental_days_left is not None and b.rental_days_left > 0 and b.day_expires_at is not None:
                            if datetime.utcnow() >= b.day_expires_at: # Check if rental day is expired
                                expired_days = ((datetime.utcnow() - b.day_expires_at).days) + 1 # Reduce rental days
                                remaining_days = b.rental_days_left - expired_days
                                if remaining_days <= 0: # If rental expired, disable charging
                                    b.rental_days_left = 0
                                    b.used_credit = 0
                                    b.day_expires_at = None

                                    if set_fm_mos_charging_off(header, b.battery_number):    # Close gate / disable charging
                                        b.charging_status = "prohibited"
                                        print("-----Charging successfully disabled due to rental expiration-----", b.battery_number)
                                    else:
                                        print("-----Failed to disable charging through API after rental expiration-----", b.battery_number)
                                    if set_fm_mos_discharging_off(header, b.battery_number):    # Close gate / disable discharging
                                        b.discharging_status = "prohibited"
                                        print("-----Discharging successfully disabled due to rental expiration-----", b.battery_number)
                                    else:
                                        print("-----Failed to disable discharging through API after rental expiration-----", b.battery_number)
                                else: # If not expired, update remaining days and reset daily credit
                                    b.rental_days_left = remaining_days
                                    b.used_credit = 0
                                    b.day_expires_at = b.day_expires_at + timedelta(days=expired_days) 
                                    
                                    if b.charging_status == 'prohibited': # Re-enable charging if it was prohibited due to rental expiration
                                        if set_fm_mos_charging_on(header, b.battery_number):
                                            b.charging_status = "granted"

                                    if b.discharging_status == 'prohibited':# Re-enable charging if it was prohibited due to rental expiration
                                        if set_fm_mos_discharging_on(header, b.battery_number):
                                            b.discharging_status = "granted"
                                    
                                b.updated_at = datetime.utcnow()
                                db.session.add(b)
                                db.session.commit()
                                send_battery_details(b.battery_number) # Send update to dashboard

                        if b.rental_days_left is not None and b.rental_days_left > 0:
                            active_limit = RENTAL_DAILY_LIMIT
                        elif b.tier is not None and str(b.tier).strip().isdigit():
                            active_limit = int(b.tier)
                        else:
                            continue

                        if b.used_credit is not None and b.used_credit >= active_limit:   # Check if limit reached
                            print("-----SOC limit reached-----", b.battery_number, "SOC:", b.SOC, "tier:", b.tier)
                            try:
                                if set_fm_mos_charging_off(header, b.battery_number):    # Close gate / disable charging
                                    b.charging_status = "prohibited"
                                    b.number_of_sessions = (b.number_of_sessions or 0) + 1
                                    print("-----Charging successfully disabled-----", b.battery_number)
                            except Exception as e:
                                print("-----Failed to disable charging through API-----", b.battery_number)
                            b.updated_at = datetime.utcnow()
                            db.session.add(b)
                            db.session.commit()
                            send_battery_details(b.battery_number) # Send update to dashboard
                        else:
                            if b.charging_status != "granted":#re-enable if somehow error occured
                                if set_fm_mos_charging_on(header, b.battery_number): # Re-enable charging
                                    b.charging_status = "granted"
                                else:
                                    b.charging_status = "failed"
                                    print("-----Failed to enable charging through API-----", b.battery_number)
                                b.updated_at = datetime.utcnow()
                                db.session.add(b)
                                db.session.commit()
                                send_battery_details(b.battery_number) # Send update to dashboard
                    except Exception as e:
                        print(f"Watcher battery error: battery={b.battery_number}, phone={b.phone_number}, error={e}")
                        db.session.rollback()
                        continue
                                
        except Exception as e:
            print("Watcher loop error:", e)

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    run()