from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

db = SQLAlchemy()

def init_app(app):
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    if 'PYTHONANYWHERE_SITE' in os.environ:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/apih99/CarRent/carrent.db'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carrent.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    # Create tables within the application context
    with app.app_context():
        db.create_all()
        # Create default admin settings if none exist
        if not AdminSettings.query.first():
            default_settings = AdminSettings()
            db.session.add(default_settings)
            db.session.commit()

# Models
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
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pickup_method = db.Column(db.String(20), nullable=False)
    delivery_address = db.Column(db.String(200), nullable=True)
    delivery_fee = db.Column(db.Float, nullable=False)
    rental_type = db.Column(db.String(20), nullable=False)

class AdminSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    min_rental_duration = db.Column(db.Integer, default=2)  # minimum hours for rental
    delivery_fee = db.Column(db.Float, default=20.0)
    late_fee_rate = db.Column(db.Float, default=10.0)  # percentage