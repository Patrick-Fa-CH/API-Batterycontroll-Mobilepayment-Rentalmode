------Creator:----------------------------------
Patrick Fässler
pfaessler@student.ethz.ch
faepatr@gmail.com
------------------------------------------------

------General Information:--------------------------------------------------------------------------------------
This project implements a backend system for controlling battery charging in combination with mobile payments. 
It connects a web interface, the Daraja (M-Pesa) API and a battery management system (BMS) through a battery API. 
The goal is to allow charging only after successful payment and only if the battery is in a safe state. 
The code is intentionally kept simple and commented, so it is recommended to go through the files and read the comments. 
To start the project, run main.py.

------System Workflow:------------------------------------------------------------------------------------------
1. The user visits the webpage https://www.charge-ewake.com
2. The user enters a charger or battery number together with a phone number
3. The selected charging option (tier or rental) is sent from the frontend to the backend
4. A payment request is triggered via the Daraja API and sent to the user’s phone
5. After a successful payment callback, the payment status is stored in the SQL database
5.1 If a smart battery is used it is directly activated through the battery API.
6. The charger sends a POST request to the server to request the charging status
7. If payment is confirmed and conditions are safe, charging is enabled and current can flow

------Project Structure:----------------------------------------------------------------------------------------
The main application logic is implemented in main.py, which handles requests and controls the overall process. 
The folder functions/ contains all API interactions and control logic such as payment handling, battery 
communication and enabling or disabling charging. Database models are defined in models/, while the frontend 
interface is located in templates/ and static/. The instance/ folder contains local data such as the database 
and is not part of the version-controlled code. SOC_Watcher.py runs as a background process and continuously 
monitors battery usage and limits.

------Tools:----------------------------------------------------------------------------------------------------
The project is written in Python using the Flask web framework and uses SQLAlchemy for database handling. 
Mobile payments are processed via the Daraja API. For local testing, Ngrok is used to expose the server to the 
internet and receive API callbacks. In production, the system runs on a VPS using Gunicorn and systemd services. 
It is recommended to use a virtual environment and store sensitive data such as API keys in a .env file.

------File structure:-------------------------------------------------------------------------------------------
│
├── functions/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── Authentification.py
│   ├── AuthentificationBattery.py
│   ├── DisableChargeBat.py
│   ├── DisableDischargeBat.py
│   ├── EnableChargeBat.py
│   ├── EnableDischargeBat.py
│   ├── GetAlarmBitBattery.py
│   ├── GetBatteryVoltageBat.py
│   ├── GetSOCBattery.py
│   ├── PaymentPush.py
│   └── TransferData.py
│
├── instance/                  <--------------is generated locally / not versioned
│   └── db.db
│
├── models/
│   └── ChargersBatterys.py
│
├── OldScripts/
│
├── static/
│
├── templates/
│   └── index.html
│
├── .env                   <--------------not in the repository (sensitive credentials)
├── .env.example
├── .gitattributes
├── .gitignore
├── main.py
├── README.txt
├── requirements.txt
└── SOC_Watcher.py