------Creator:----------------------------------
Patrick Fässler
pfaessler@student.ethz.ch
faepatr@gmail.com
------------------------------------------------

------General Information:--------------------------------------------------------------------------------------
I tried to keep the code as simple as possible and equip it with comments. It really make sense
to go into the files and read the comments first. To start the project run the main.py file.
Have a look on the frontend templates/index.html file and on the functions.

------This Python project can be split in the following process:-------------------------------------------------

0. Visit the page https://www.charge-ewake.com
1. Put in the charger number and the phone number in the UI
2. Select amount to charge to send all the information from the frontend to the backend
3. User gets payment request on phone-number through Daraja API
4. After successfull Callback from API, payment status is stored in SQL database
5. Start button on charger is pressed and charger sends POST request to server to get charging status
6. After receiving charging status granted, charger open gate and allows charging current to flow

-------Tools:----------------------------------------------------------------------------------------------------
As in any project it is recommended to run this project in an virtual environement. For testing on local host, 
the webframework FLASK is used. For accessing online through https, NGROK is used to create a tunnel to the internet.
This is needed to receive callbacks from APIs. For the payment process the daraja-API is use. 
Later a VPS from Exoscale (CH) was set up. More information about the Ports, Proxy ect are in the main.py file

------File structure:-------------------------------------------------------------------------------------------
    
    ├── README.md
    ├── main.py                     (used to process POST & GET requests from website and call functions)
    │   └── README.md
    ├── templates
    │   └── index.htm               (creates html website and sends POST requests to main.py)
    ├── functions
    │   ├── __init.py__
    │   ├── Authentification.py     (creates access token and is used for all daraja APIs)
    │   └── PaymentPush.py          (sends payment request to daraja API server)
    │
    ├── OldScripts                  (experiments)
    ├── .venv                       (virtual environement)
    ├── .ideas