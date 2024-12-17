from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Email Configuration
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'hafiz.kelkes@gmail.com'  # Replace with your Gmail address
MAIL_PASSWORD = 'wuom blzl ilfr wyye'  # Replace with your Gmail app password
MAIL_DEFAULT_SENDER = 'wuom blzl ilfr wyye'  # Replace with your Gmail address

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    license_plate = db.Column(db.String(20), unique=True, nullable=False)
    daily_rate = db.Column(db.Float, nullable=False)
    hourly_rate = db.Column(db.Float, nullable=False)
    reservations = db.relationship('Reservation', backref='car', lazy=True)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    pickup_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pickup_method = db.Column(db.String(20), nullable=False)  # 'setiawangsa' or 'delivery'
    delivery_address = db.Column(db.Text, nullable=True)  # Required if pickup_method is 'delivery'
    delivery_fee = db.Column(db.Float, default=0)  # Will be 20 if delivery is chosen
    rental_type = db.Column(db.String(10), nullable=False, default='daily')  # 'hourly' or 'daily'

def init_app(app):
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carrent.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Email configuration
    app.config['MAIL_SERVER'] = MAIL_SERVER
    app.config['MAIL_PORT'] = MAIL_PORT
    app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
    app.config['MAIL_USERNAME'] = MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
    app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER
    
    db.init_app(app)
    with app.app_context():
        db.create_all() 