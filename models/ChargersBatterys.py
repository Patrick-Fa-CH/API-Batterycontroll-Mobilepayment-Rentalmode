from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()
#creating the database. Each charger has columns: charger_number, phone_number, tier, payment_status, charging_status
class charger(db.Model):  
    __tablename__ = "chargers" 

    charger_number = db.Column(db.String(32), primary_key=True)
    phone_number = db.Column(db.String(16), nullable=True)
    tier = db.Column(db.String(8), nullable=True)
    payment_status = db.Column(db.String(16), nullable=False, default="waiting")  # waiting|success|failed
    charging_status = db.Column(db.String(16), nullable=False, default="prohibited")  # prohibited|granted
    checkout_request_id = db.Column(db.String(128), nullable=True, unique=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    def touch(self):
        self.updated_at = datetime.utcnow()

#curl -k -X POST -d "" "https://dev.iov18.com/api/Login/Authenticate?Username=faepatr@gmail.com&Password=1234567A"
class Battery(db.Model):  #this database is for intern eWAKA use. Not directly related to the charger project
    __tablename__ = "motorbike_batteries"

    phone_number = db.Column(db.String(16), nullable=True)
    battery_number = db.Column(db.String(32), primary_key=True)
    payment_status = db.Column(db.String(16), nullable=False, default="waiting")  # waiting|success|failed
    tier = db.Column(db.String(8), nullable=True)
    rental_days_left = db.Column(db.Integer, nullable=True, default=0)
    day_expires_at = db.Column(db.DateTime, nullable=True)
    charging_status = db.Column(db.String(16), nullable=False, default="prohibited")  # prohibited|granted|loading|failed enable charging
    discharging_status = db.Column(db.String(16), nullable=False, default="granted")  # prohibited|granted|failed enable discharging
    SOC = db.Column(db.Integer, nullable=True, default=0) # state of charge of battery, only 
    used_credit = db.Column(db.Integer, nullable=True, default=0) # used credit of tier in %
    number_of_sessions = db.Column(db.Integer, nullable=True, default=0)
    number_of_cycles = db.Column(db.Float, nullable=True, default=0.0)
    checkout_request_id = db.Column(db.String(128), nullable=True, unique=True)
    last_payment_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    def touch(self):
        self.updated_at = datetime.utcnow()
class BatteryAdditionalData(db.Model):
    __bind_key__ = "battery_extra"
    __tablename__ = "battery_additional_data"

    battery_number = db.Column(db.String(32),primary_key=True)

    last_payment_amount = db.Column(db.Numeric(10, 2),nullable=True)
    reserve_1 = db.Column(db.Text, nullable=True)
    reserve_2 = db.Column(db.Text, nullable=True)
    reserve_3 = db.Column(db.Text, nullable=True)
    reserve_4 = db.Column(db.Text, nullable=True)
    reserve_5 = db.Column(db.Text, nullable=True)


