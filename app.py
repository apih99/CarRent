from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import config
from config import db, Car, Reservation, AdminSettings

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
        rental_type = request.form.get('rental_type', 'daily')
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
            delivery_fee=delivery_fee,
            rental_type=rental_type
        )
        db.session.add(reservation)
        db.session.commit()

        return redirect(url_for('payment_confirmation', reservation_id=reservation.id))

    # Get only available cars
    cars = Car.query.all()
    admin_settings = AdminSettings.query.first()
    return render_template('make_reservation.html', cars=cars, admin_settings=admin_settings)

@app.route('/payment_confirmation/<int:reservation_id>')
def payment_confirmation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    car = Car.query.get(reservation.car_id)
    admin_settings = AdminSettings.query.first()
    
    # Calculate total amount
    duration = (reservation.return_date - reservation.pickup_date).total_seconds()
    if reservation.rental_type == 'hourly':
        duration = duration / 3600  # Convert to hours
        rate = car.hourly_rate
    else:
        duration = duration / 86400  # Convert to days
        rate = car.daily_rate
    
    total_amount = (duration * rate) + reservation.delivery_fee
    
    # Set payment deadline to 1 hour from now
    payment_deadline = datetime.now() + timedelta(hours=1)

    return render_template(
        'payment_confirmation.html',
        reservation=reservation,
        car=car,
        admin_settings=admin_settings,
        total_amount=total_amount,
        payment_deadline=payment_deadline.isoformat()
    )

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

@app.route('/admin')
def admin():
    cars = Car.query.all()
    reservations = Reservation.query.order_by(Reservation.created_at.desc()).all()
    return render_template('admin.html', cars=cars, reservations=reservations)

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

        return redirect(url_for('admin'))

@app.route('/admin/update_reservation_status/<int:reservation_id>', methods=['POST'])
def update_reservation_status(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    new_status = request.json.get('status')
    reservation.status = new_status

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': f'Reservation {new_status} successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating reservation status.'}), 500

application = app