from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import config
from config import db, Car, Reservation

app = Flask(__name__)
config.init_app(app)

@app.route('/')
def index():
    cars = Car.query.all()
    # Get next 7 days for availability display
    dates = [(datetime.now() + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(7)]
    return render_template('index.html', cars=cars, dates=dates)

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
        delivery_fee = 20.0 if pickup_method == 'delivery' else 0.0

        # Check if car is available for the selected dates
        existing_reservations = Reservation.query.filter_by(car_id=car_id, status='approved').filter(
            ((Reservation.pickup_date <= pickup_date) & (Reservation.return_date >= pickup_date)) |
            ((Reservation.pickup_date <= return_date) & (Reservation.return_date >= return_date)) |
            ((Reservation.pickup_date >= pickup_date) & (Reservation.return_date <= return_date))
        ).first()

        if existing_reservations:
            flash('Sorry, this car is not available for the selected dates.', 'danger')
            return redirect(url_for('make_reservation'))

        reservation = Reservation(
            car_id=car_id,
            student_id=student_id,
            email=email,
            phone=phone,
            pickup_date=pickup_date,
            return_date=return_date,
            pickup_method=pickup_method,
            delivery_address='UPNM' if pickup_method == 'delivery' else None,
            delivery_fee=delivery_fee
        )
        db.session.add(reservation)
        db.session.commit()
        flash('Reservation submitted successfully! Waiting for approval.', 'success')
        return redirect(url_for('index'))

    # Get only available cars
    cars = Car.query.all()
    return render_template('make_reservation.html', cars=cars)

@app.route('/check_availability/<int:car_id>')
def check_availability(car_id):
    # Get approved reservations for the car
    reservations = Reservation.query.filter_by(car_id=car_id, status='approved').all()
    reserved_dates = [
        {
            'start': res.pickup_date.strftime('%Y-%m-%d %H:%M'),
            'end': res.return_date.strftime('%Y-%m-%d %H:%M')
        }
        for res in reservations
    ]
    return {'reserved_dates': reserved_dates}

if __name__ == '__main__':
    app.run(debug=True, port=5000) 