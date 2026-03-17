### ----DEVELEPTER INFOS-------------------------------------------------------------  ###
### This code was developed by:
### Patrick Fässler, ETH Zurich, 2024
### Github: https://github.com/Patrick-Fa-CH
### Email:  faepatr@gmailcom

### ----GENERAL INFOS------------------------------------------------------------------------- ### 
### For develeppment a Flask Web app was used. It was made accessible to internet through a tunnel by NGROK ###
### For the APIs to work a https Callback URL is needed, therefore NGROK was used###
### A VPS from Exoscale (CH) is used for production hosting and nginx as reverse proxy. ###
### In production the Flask Web app is operatet through Unicorn. ###
### The VPS has a PostgreSQL database, which is accessed through SQLAlchemy in the Flask Web app. ###
### The VPS listenes on port 80 and 443. Port 80 is for HTTP (for charger SIMmodule) and port 443 is for HTTPS ###

### ----USEFUL COMMANDS FOR VPS INTERACTION------------------------------------------------------------- ###
### ssh ubuntu@159.100.252.158  --- SSH connection to VPS (First command to access VPS, SSH key is needed, ask developer for access)
### ssh ubuntu@139.59.159.158 --- SSH connection to VPS of eWAKA (First command to access VPS, integration of pub SSH key is needed, ask Leonard)
### cd ~/app --- Go to app folder
### ls --- List files in folder
### cd /home/ubuntu/app/instance --- Go to instance folder, where the SQL database is stored
### sqlite3 db.db --- Access SQLlite database, command only works in instance folder, where the database is stored
### sudo journalctl -u gunicorn -f --- Access logs of Gunicorn and see Flask routes)
### sudo tail -f /var/log/nginx/access.log --- Access logs of Nginx and see server requests)
### sudo nano /etc/nginx/sites-available/charger --- Edit Nginx config file
### sudo nano /etc/systemd/system/gunicorn.service --- Edit Gunicorn service file
### sudo systemctl status gunicorn --- Cheching if Gunicorn is running 
### sudo systemctl daemon-reload --- Reload Gunicorn after changes in settings 
### sudo systemctl reload nginx --- Reload Nginx after changes in code
### sudo ss -lntp --- Check if ports 80 and 443 are listening
"""----Simulation of input from frontend in cmd---------------------------------------
curl -k -X POST https://charge-ewaka.com/Save/Input -H "Content-Type: application/json" -d "{\"charger_number\":\"\",\"battery_number\":\"051111111111\",\"phone_number\":\"254119456993\",\"tier\":\"\",\"rental_days\":\"2\"}"
curl -k -X POST https://charge-ewaka.com/Save/Input -H "Content-Type: application/json" -d "{\"charger_number\":\"1111\",\"battery_number\":\"\",\"phone_number\":\"254119456993\",\"tier\":\"20\",\"rental_days\":\"\"}"
-------------------------------------------------------------------------------"""

""" ---Commands for SQLlite database (after sqlite3 db.db activated):----------
 cd /home/ubuntu/app/instance
 sqlite3 db.db
 
 .header on
 .mode column
 SELECT * FROM chargers; --- Show content of chargers table (after .tables)
 SELECT * FROM motorbike_batteries; --- Show content of batteries table (after .tables)
 .exit --- Exit SQLlite database
 .tables --- List tables in database
 .schema chargers --- Show structure of chargers table
    -----------------------------------------------------------------------------"""

""" -------Update files through git:---------------------------------------------
cd ~/app
git pull   
sudo systemctl restart gunicorn
sudo systemctl restart soc-watcher
    -----------------------------------------------------------------------------"""

import flask 
import json
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, Response

#Import functions from function folder
from dotenv import load_dotenv
from pathlib import Path
from functions.Authentification import AuthHead 
from functions.AuthentificationBattery import AuthHeadBat
from functions.PaymentPush import PaymentPush
from functions.EnableChargeBat import set_fm_mos_charging_on
from functions.EnableDischargeBat import set_fm_mos_discharging_on  
from functions.GetSOCBattery import get_battery_soc
from functions.TransferData import send_battery_details, send_charger_details
from models.ChargersBatterys import db, Battery, charger


print("-------------------Start of Master-Thesis ETH Python Script-------------------")

BASE_DIR = Path(__file__).resolve().parent #make link to .env file, which is needed for environment variables
load_dotenv(BASE_DIR / ".env")
#definition of some global variables, which can be set through environment variables, otherwise default values are used
allowed_tiers = os.environ.get("ALLOWED_TIERS", "20,40,70,80,100").split(",") #allowed tiers for charging, can be set through environment variable, default are 20, 40, 70, 80 and 100
allowed_tiers = set(allowed_tiers)
BYPASS_PHONE_NUMBER_ONE = os.environ.get("BYPASS_PHONE_NUMBER_ONE") #bypass phone number for internal charging. ONLY TRUSTY NUMBER!
BYPASS_PHONE_NUMBER_TWO = os.environ.get("BYPASS_PHONE_NUMBER_TWO") #bypass phone number for internal charging. ONLY TRUSTY NUMBER!
maximum_rental_days = int(os.environ.get("MAXIMUM_RENTAL_DAYS", "30")) #maximum rental days for battery rental
charger_number_length = int(os.environ.get("CHARGER_NUMBER_LENGTH", "4"))
battery_number_length = int(os.environ.get("BATTERY_NUMBER_LENGTH", "12"))
phone_number_length = int(os.environ.get("PHONE_NUMBER_LENGTH", "12"))

app = Flask(__name__)
#Database setup, using SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///db.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context(): #creating the databes
    db.create_all()

#standart route for website
@app.route('/')
def index():
    return render_template('index.html')


#route for getting the inputs from frontend. Returns 0 if the input is valid.
@app.route("/Save/Input", methods=["POST"])
def save_input():
    try:
        data = request.get_json() or {} #get data from frontend, if no data is sent, use empty dict as default
        
        charger_number = (data.get("charger_number") or "").strip()
        battery_number = (data.get("battery_number") or "").strip()
        phone_number   = (data.get("phone_number") or "").strip()
        tier           = (data.get("tier") or "").strip()
        rental_days_raw = (data.get("rental_days") or "").strip()
        rental_days_left = int(rental_days_raw) if rental_days_raw.isdigit() else 0

        print("-----Received information from frontend: ", 
              "charger:", charger_number, "battery:", battery_number,
              "phone:", phone_number, "tier:", tier, "rental_days:", rental_days_left)
        
        #---------------start basic validation if input----------------------------------
        
        charger_given = len(charger_number) > 0
        battery_given = len(battery_number) > 0
        tier_given = len(tier) > 0
        rental_given = rental_days_left > 0
        phone_valid = phone_number.isdigit() and len(phone_number) == phone_number_length
        charger_valid = charger_number.isdigit() and len(charger_number) == charger_number_length
        battery_valid = battery_number.isdigit() and len(battery_number) == battery_number_length
        tier_valid = tier in allowed_tiers
        rental_valid = 0 <= rental_days_left <= maximum_rental_days
        
        if charger_given and battery_given :
            return jsonify({"ResponseCode": "1", "error": "Input error: Received charger- and batterynumber. Only one input allowed"}), 400
        if (not charger_given) and (not battery_given):
            return jsonify({"ResponseCode": "1", "error": "Input error: Missing chargernumber or batterynumber. At least one is needed"}), 400
        if charger_given:
            if not tier_given:
                return jsonify({"ResponseCode": "1","error": "Input error: Charger requires a tier."}), 400
            if rental_given:
                return jsonify({"ResponseCode": "1","error": "Input error: Charger mode does not allow rental_days."}), 400
        if battery_given:
            if tier_given and rental_given:
                return jsonify({"ResponseCode": "1","error": "Input error: Choose either tier or rental_days, not both."}), 400
            if (not tier_given) and (not rental_given):
                return jsonify({"ResponseCode": "1","error": "Input error: Battery requires either tier or rental_days."}), 400
        
        if tier_given and not tier_valid:
            return jsonify({"ResponseCode": "1", "error": f"Invalid tier. Allowed values are {allowed_tiers}"}), 400
        if not phone_valid:
            return jsonify({"ResponseCode": "1", "error": "Invalid phonenumber. Must be in format 2547xxxxxxxx"}), 400
        if not rental_valid:
            return jsonify({"ResponseCode": "1", "error": f"Invalid rental days. Must be between 0 and {maximum_rental_days}"}), 400
        #-----------------end basic validation if input----------------------------------
        #validation of charger number and storing in charger database 
        if charger_given:
            if not charger_valid:
                return jsonify({"ResponseCode": "1", "error": f"Invalid chargernumber. Must be a {charger_number_length}-digit number"}), 400

            update = charger.query.get(charger_number)
            if update is None:
                update = charger(
                    charger_number=charger_number, #default setup for new charger
                    phone_number=phone_number,
                    tier=tier,
                    payment_status="waiting",
                    charging_status="prohibited"
                )
            update.phone_number = phone_number #update dataset if charger exists
            update.tier = tier
            update.payment_status = "waiting"
            update.charging_status = "prohibited"
            update.touch()
            db.session.add(update)
            db.session.commit()
            print("-----Charger DB updated-----", charger_number, phone_number, tier)

            auto_payment =data.get("auto_payment", True) #if UI from from Web is used, auto_payment is deactivated
            if auto_payment not in [False, "false", "False", "0"]:
                return payment_push()
            return jsonify({"ResponseCode": "0", "mode": "charger"})
        
        #validation of battery number and storing in battery database
        else:
            if not battery_valid:
                return jsonify({"ResponseCode": "1", "error": f"Invalid batterynumber. Must be a {battery_number_length}-digit number"}), 400

            update = Battery.query.get(battery_number)
            if update is None:
                update = Battery(
                    phone_number=phone_number,
                    battery_number = battery_number,
                    payment_status="waiting",
                    tier=tier,
                    rental_days_left=rental_days_left,
                    day_expires_at= None,
                    charging_status="prohibited",
                    discharging_status = "granted",
                    SOC = None,
                    used_credit = 0,
                    checkout_request_id = None,
                    updated_at = None
                )
            update.phone_number = phone_number
            update.tier = tier
            update.rental_days_left = rental_days_left
            update.payment_status = "waiting"
            update.charging_status = "prohibited"
            try:
                if battery_given:
                    headerBat = AuthHeadBat()
                    SOC =get_battery_soc(headerBat, update.battery_number, 15)
                    if SOC > 70:
                        return jsonify({"ResponseCode": "1","error": "Couldnt get a valid SOC under 70%/ from the battery"}), 400
            except (TypeError, KeyError):
                print("-----Error during getting SOC of Battery-----", data)
                return jsonify({"ResponseCode": "1", "error": "Error during getting SOC from Battery."}), 400
            
            update.touch()
            db.session.add(update)
            db.session.commit()
            print("-----Battery DB updated-----", battery_number, phone_number, tier,rental_days_left)
            

            auto_payment =data.get("auto_payment", True) #if UI from my API index Web is used, auto_payment is deactivated
            if auto_payment not in [False, "false", "False", "0"]:
                return payment_push()
            return jsonify({"ResponseCode": "0", "mode": "battery"})

    except (TypeError, KeyError):
        return jsonify({"ResponseCode": "1"}), 400
    except Exception as e:
        db.session.rollback()
        print("DB error:", e)
        return jsonify({"ResponseCode": "1"}), 500


#route for pushing the "request payment" button. The payment request is sent to the API.
#It returns response from API. (ResponseCode 0 = success)
@app.route("/Payment/Push/Request", methods=["POST"])
def payment_push():
    
    try:
        data = request.get_json() or {} #read data from frontend
        
        charger_number = (data.get("charger_number") or "").strip()
        battery_number = (data.get("battery_number") or "").strip()
        phone_number   = (data.get("phone_number") or "").strip()
        tier           = (data.get("tier") or "").strip()
        rental_days_raw = (data.get("rental_days") or "").strip()
        rental_days_left = int(rental_days_raw) if rental_days_raw.isdigit() else 0
        charger_given = len(charger_number) > 0
        battery_given = len(battery_number) > 0
        if charger_given and battery_given:
            return jsonify({"ResponseCode": "1", "error": "Input error: Received charger- and batterynumber"}), 400
        if (not charger_given) and (not battery_given):
            return jsonify({"ResponseCode": "1", "error": "Input error: Missing charger_number/battery_number"}), 400

        header = AuthHead() #get tooken for API access and create header for API request
        SMSPushResponse = PaymentPush(header, phone_number, tier, rental_days_left)
        ResponseCode = str(SMSPushResponse.get("ResponseCode", ""))
        CheckoutRequestID = str(SMSPushResponse.get("CheckoutRequestID", ""))
        
        #update charger or battery database with checkoutID, which is needed for matching the callback from MPesa with the payment request
        if charger_given:
            update = charger.query.get(charger_number)
            if update is None:
                return jsonify({"ResponseCode": "1", "error": "unknown charger_number"}), 404
        else:        
            update = Battery.query.get(battery_number)
            if update is None:
                return jsonify({"ResponseCode": "1", "error": "unknown battery_number"}), 404

        update.checkout_request_id = CheckoutRequestID
        update.touch()
        db.session.add(update)
        db.session.commit()

        if ResponseCode == "0":
            print("-----Server send payment request successfull-----", "mode:", ("charger" if charger_given else "battery"))
        else:
            print("-----Server could not send payment request-----")
            print(SMSPushResponse)

        return jsonify(SMSPushResponse)

    except (TypeError, KeyError):
        print("-----Error during payment push request-----", data)
        return jsonify({"ResponseCode": "1"}), 400
    except Exception as e:
        db.session.rollback()
        print("DB error:", e)
        return jsonify({"ResponseCode": "1"}), 500
    
#route to receive callback from MPesa, first checking structure and 
#than checking if payment was successfull (ResultCode = 0)
@app.route("/mpesa/callback", methods=["POST"])
def mpesa_callback(): 

    try:
        
        data = request.get_json() or {} #stuff from frontend
        CheckoutRequestID = str(data.get("Body",{}).get("stkCallback",{}).get("CheckoutRequestID",{}))
        ResultCode = str(data.get("Body",{}).get("stkCallback",{}).get("ResultCode"))

        if ResultCode == "0":
            #if payment was successfull, first search in charger database for matching checkoutID and update DB
            update_charger = charger.query.filter_by(checkout_request_id=CheckoutRequestID).first()
            if update_charger is not None:
                update_charger.payment_status  = "success"
                update_charger.charging_status = "granted"
                update_charger.touch()
                db.session.add(update_charger)
                db.session.commit()
                send_charger_details(update_charger.charger_number)
                print("-----Server received and stored payment confirmation (CHARGER)-----")
                return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

            #if no matching checkoutID in charger database, search in battery database and update DB and activate Battery
            update_battery = Battery.query.filter_by(checkout_request_id=CheckoutRequestID).first()
            if update_battery is not None:
                update_battery.payment_status  = "success"
                update_battery.last_payment_at = datetime.utcnow()
                update_battery.used_credit = 0
                update_battery.touch()
                db.session.add(update_battery)
                db.session.commit()
                print("-----Server received and stored payment confirmation (BATTERY)-----")

                try:
                    header = AuthHeadBat() #get token for battery API access
                    if set_fm_mos_charging_on(header, update_battery.battery_number): #activate battery through API
                        update_battery.charging_status = "granted"
                        if update_battery.rental_days_left is not None and update_battery.rental_days_left > 0:
                            update_battery.used_credit = 0
                            update_battery.day_expires_at = datetime.utcnow() + timedelta(days=1)
                    else:
                        update_battery.charging_status = "failed"
                        print("-----Server failed to enable charging on battery ",update_battery.battery_number," (BATTERY)-----")
                except:
                    update_battery.charging_status = "failed"
                    print("-----Server failed during enabling proxess ",update_battery.battery_number," (BATTERY)-----")
                try:
                    if update_battery.discharging_status  == 'prohibited':#ensure activ discharging through API
                        set_fm_mos_discharging_on(header, update_battery.battery_number)
                        update_battery.discharging_status = "granted"
                    else:
                        update_battery.discharging_status = "failed"
                        print("-----Server failed to enable discharging on battery ",update_battery.battery_number," (BATTERY)-----")
                except:
                    print("-----Server failed during enabling discharging process ",update_battery.battery_number," (BATTERY)-----")

                SOC = get_battery_soc(header, update_battery.battery_number) #get SOC of battery through API
                if SOC is not None:
                    update_battery.SOC = int(SOC)
                update_battery.touch()
                db.session.add(update_battery)
                db.session.commit()
                send_battery_details(update_battery.battery_number)
                print("-----Server sent battery info (BATTERY)-----")
                return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

            print("-----Callback not matched-----", CheckoutRequestID)
            return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

        else:
            #if payment was not successfull, first search in charger database for matching checkoutID and update DB
            update_charger = charger.query.filter_by(checkout_request_id=CheckoutRequestID).first()
            if update_charger is not None:
                update_charger.payment_status = "failed"
                update_charger.touch()
                db.session.add(update_charger)
                db.session.commit()
                send_charger_details(update_charger.charger_number)
                print("-----Server sent battery info (BATTERY)-----")
                print("-----Server received payment failure (CHARGER)-----")
                print(data)
                return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})
            #if no matching checkoutID in charger database, search in battery database and update DB
            update_battery = Battery.query.filter_by(checkout_request_id=CheckoutRequestID).first()
            if update_battery is not None:
                update_battery.payment_status = "failed"
                update_battery.touch()
                db.session.add(update_battery)
                db.session.commit()
                send_battery_details(update_battery.battery_number)
                print("-----Server sent battery info (BATTERY)-----")
                print("-----Server received payment failure (BATTERY)-----")
                print(data)
                return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

            print("-----Callback not matched-----", CheckoutRequestID)
            return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})
        
    except Exception as e:
        db.session.rollback()
        print("DB error:", e), 500
    #returning successfull callback receivement to MPesa
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})


#route for charger to access payment status 
@app.route('/Incoming/Charging/Request', methods=['POST'])
def ChargingRequest():
    try:
        print('-----Received charging request-----')
        data = request.get_json() or {} #get charger number from charger
        charger_number = str((data.get("charger_number") or "").strip())

        update = charger.query.get(charger_number) #update database of charger
        if update is None:
            return jsonify({"ChargingStatus": "prohibited", "Tier": None}), 404
        tier = update.tier
        if update.payment_status == "success":
            update.payment_status = "waiting" #resetting status
            update.charging_status = "loading" #resetting status
            update.touch()
            db.session.add(update)
            db.session.commit()
            send_charger_details(update.charger_number) #send update to dashboard
            print('-----Charging granted-----')
            return jsonify({"ChargingStatus": "granted", "Tier": tier}), 200
        else: 
            return jsonify({"ChargingStatus": "prohibited", "Tier": tier}), 200
    except (TypeError, KeyError):
        print("-----Invalid charging request structure:-----", data)
        return jsonify({"ChargingStatus": "prohibited", "Tier": tier}), 400
    except Exception as e:
        db.session.rollback()
        print("DB error:", e)
        return jsonify({"ChargingStatus": "prohibited", "Tier": tier}), 500
#route for frontend to check payment status
@app.route("/Payment/Status", methods=['POST'])
def status():
    try:
        data = request.get_json() or {} #get data from frontend
        charger_number = str((data.get("charger_number") or "").strip())
        battery_number = str((data.get("battery_number") or "").strip())

        if charger_number: #return payment status of charger if charger number is given
            update = charger.query.get(charger_number)
            return jsonify({"status": (update.payment_status if update else "waiting")})

        if battery_number: #return payment status of battery if battery number is given
            update = Battery.query.get(battery_number)
            return jsonify({"status": (update.payment_status if update else "waiting")})

        return jsonify({"status": "waiting"})
    except Exception:
        return jsonify({"status": "waiting"})
@app.route("/Charger/Status", methods=['POST'])
def chargingstatus():
    try:
        data = request.get_json() or {}
        charger_number = str((data.get("charger_number") or "").strip())
        battery_number = str((data.get("battery_number") or "").strip())

        if charger_number: #return charging status of charger if charger number is given
            update = charger.query.get(charger_number)
            return jsonify({"status": (update.charging_status if update else "waiting")})

        if battery_number: #return charging status of battery if battery number is given
            update = Battery.query.get(battery_number)
            return jsonify({"status": (update.charging_status if update else "waiting")})

        return jsonify({"status": "waiting"})
    except Exception:
        return jsonify({"status": "waiting"})

#starting the local host on port 5000
if __name__ == "__main__": #if statment, safety feature for running the server
    app.run(host= '0.0.0.0', port = 5000)



