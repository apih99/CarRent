from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carrent.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
    status = db.Column(db.String(20), default='pending')  # pending, approved, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pickup_method = db.Column(db.String(20), nullable=False)
    delivery_fee = db.Column(db.Float, nullable=False)
    rental_type = db.Column(db.String(20), nullable=False)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    cars = Car.query.all()
    reservations = Reservation.query.order_by(Reservation.created_at.desc()).all()
    return render_template('admin.html', cars=cars, reservations=reservations)

@app.route('/make_reservation', methods=['GET', 'POST'])
def make_reservation():
    if request.method == 'POST':
        car_id = request.form.get('car_id')
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        phone = request.form.get('phone')
        pickup_date = datetime.strptime(request.form.get('pickup_date'), '%Y-%m-%dT%H:%M')
        return_date = datetime.strptime(request.form.get('return_date'), '%Y-%m-%dT%H:%M')
        pickup_method = request.form.get('pickup_method')
        rental_type = request.form.get('rental_type')  # Get rental type

        # Validate minimum rental duration
        duration = return_date - pickup_date
        if rental_type == 'hourly':
            min_duration = timedelta(hours=2)
            if duration < min_duration:
                flash('Minimum rental duration for hourly rentals is 2 hours', 'error')
                return redirect(url_for('make_reservation'))
        else:  # daily rental
            if duration < timedelta(hours=24):
                flash('For daily rentals, minimum duration is 1 day', 'error')
                return redirect(url_for('make_reservation'))

        # Set delivery fee based on pickup method
        delivery_fee = 20 if pickup_method == 'delivery' else 0

        # Create new reservation
        new_reservation = Reservation(
            student_id=student_id,
            email=email,
            phone=phone,
            pickup_date=pickup_date,
            return_date=return_date,
            car_id=car_id,
            pickup_method=pickup_method,
            delivery_fee=delivery_fee,
            rental_type=rental_type  # Save rental type
        )

        try:
            db.session.add(new_reservation)
            db.session.commit()
            flash('Reservation submitted successfully! Please wait for approval.', 'success')
            return redirect(url_for('user_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your reservation.', 'error')
            return redirect(url_for('make_reservation'))

    # GET request - show the reservation form
    cars = Car.query.all()
    return render_template('make_reservation.html', cars=cars)

@app.route('/admin/approve/<int:reservation_id>')
def approve_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = 'approved'
    db.session.commit()
    flash('Reservation approved!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/reject/<int:reservation_id>')
def reject_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = 'rejected'
    db.session.commit()
    flash('Reservation rejected!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/add_car', methods=['POST'])
def add_car():
    if request.method == 'POST':
        model = request.form.get('model')
        year = request.form.get('year')
        license_plate = request.form.get('license_plate')
        daily_rate = request.form.get('daily_rate')
        hourly_rate = request.form.get('hourly_rate')

        new_car = Car(
            model=model,
            year=year,
            license_plate=license_plate,
            daily_rate=daily_rate,
            hourly_rate=hourly_rate
        )

        try:
            db.session.add(new_car)
            db.session.commit()
            flash('Car added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding car. Please try again.', 'error')

        return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_car/<int:car_id>', methods=['POST'])
def edit_car(car_id):
    car = Car.query.get_or_404(car_id)
    
    car.model = request.form.get('model')
    car.year = request.form.get('year')
    car.license_plate = request.form.get('license_plate')
    car.daily_rate = request.form.get('daily_rate')
    car.hourly_rate = request.form.get('hourly_rate')

    try:
        db.session.commit()
        flash('Car updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating car. Please try again.', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_car/<int:car_id>')
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)
    
    try:
        db.session.delete(car)
        db.session.commit()
        flash('Car deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting car. Please try again.', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_reservation_status/<int:reservation_id>', methods=['POST'])
def update_reservation_status():
    reservation_id = request.json.get('reservation_id')
    new_status = request.json.get('status')
    
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = new_status

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': f'Reservation {new_status} successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating reservation status.'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 