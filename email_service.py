from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

def send_reservation_notification(reservation):
    """Send email notification about reservation status"""
    subject = f'Car Rental Reservation {reservation.status.capitalize()}'
    
    # Create appropriate message based on status
    if reservation.status == 'approved':
        message_body = f"""
Dear {reservation.student_id},

Your car rental reservation has been APPROVED!

Reservation Details:
- Car: {reservation.car.model}
- Pickup Date: {reservation.pickup_date.strftime('%Y-%m-%d %H:%M')}
- Return Date: {reservation.return_date.strftime('%Y-%m-%d %H:%M')}
- Rental Type: {reservation.rental_type.capitalize()}
- Pickup Method: {reservation.pickup_method}

Please make sure to pick up the car at the scheduled time.

Thank you for choosing our service!

Best regards,
Car Rental Team
"""
    else:  # rejected
        message_body = f"""
Dear {reservation.student_id},

Unfortunately, your car rental reservation has been REJECTED.

Reservation Details:
- Car: {reservation.car.model}
- Pickup Date: {reservation.pickup_date.strftime('%Y-%m-%d %H:%M')}
- Return Date: {reservation.return_date.strftime('%Y-%m-%d %H:%M')}
- Rental Type: {reservation.rental_type.capitalize()}

You can try making a new reservation with different dates or choose a different car.

Thank you for your understanding.

Best regards,
Car Rental Team
"""

    try:
        msg = Message(
            subject=subject,
            recipients=[reservation.email],
            body=message_body
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False 