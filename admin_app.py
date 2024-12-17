from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import config
from config import db, Car, Reservation
from functools import wraps
from email_service import mail, send_reservation_notification

app = Flask(__name__)
config.init_app(app)
mail.init_app(app)

# Simple admin authentication (you might want to enhance this in production)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return ('Could not verify your access level for that URL.\n'
                   'You have to login with proper credentials', 401,
                   {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@admin_required
def admin():
    cars = Car.query.all()
    reservations = Reservation.query.order_by(Reservation.created_at.desc()).all()
    return render_template('admin.html', cars=cars, reservations=reservations)

@app.route('/add_car', methods=['POST'])
@admin_required
def add_car():
    model = request.form.get('model')
    year = request.form.get('year')
    license_plate = request.form.get('license_plate')
    daily_rate = request.form.get('daily_rate')

    car = Car(
        model=model,
        year=year,
        license_plate=license_plate,
        daily_rate=daily_rate
    )
    db.session.add(car)
    try:
        db.session.commit()
        flash('Car added successfully!', 'success')
    except:
        db.session.rollback()
        flash('Error: License plate must be unique!', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/admin/edit_car/<int:car_id>', methods=['POST'])
@admin_required
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
    except:
        db.session.rollback()
        flash('Error: License plate must be unique!', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/delete_car/<int:car_id>')
@admin_required
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)
    if car.reservations:
        flash('Cannot delete car with existing reservations!', 'danger')
    else:
        db.session.delete(car)
        db.session.commit()
        flash('Car deleted successfully!', 'success')
    
    return redirect(url_for('admin'))

@app.route('/approve_reservation/<int:reservation_id>')
@admin_required
def approve_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    
    # Check if car is available for these dates
    existing_reservations = Reservation.query.filter_by(
        car_id=reservation.car_id, 
        status='approved'
    ).filter(
        ((Reservation.pickup_date <= reservation.pickup_date) & (Reservation.return_date >= reservation.pickup_date)) |
        ((Reservation.pickup_date <= reservation.return_date) & (Reservation.return_date >= reservation.return_date)) |
        ((Reservation.pickup_date >= reservation.pickup_date) & (Reservation.return_date <= reservation.return_date))
    ).first()

    if existing_reservations:
        flash('Cannot approve: Car is already reserved for these dates!', 'danger')
    else:
        reservation.status = 'approved'
        db.session.commit()
        # Send email notification
        if send_reservation_notification(reservation):
            flash('Reservation approved and notification sent!', 'success')
        else:
            flash('Reservation approved but failed to send notification.', 'warning')
    
    return redirect(url_for('admin'))

@app.route('/reject_reservation/<int:reservation_id>')
@admin_required
def reject_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = 'rejected'
    db.session.commit()
    # Send email notification
    if send_reservation_notification(reservation):
        flash('Reservation rejected and notification sent!', 'success')
    else:
        flash('Reservation rejected but failed to send notification.', 'warning')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, port=5001) 