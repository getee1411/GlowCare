from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
import uuid
from datetime import datetime
from model import db, Payment

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Service URLs
APPOINTMENT_SERVICE_URL = 'http://localhost:5002'

with app.app_context():
    db.create_all()

@app.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    
    # Generate payment reference
    payment_reference = f"PAY-{uuid.uuid4().hex[:8].upper()}"
    
    payment = Payment(
        user_id=data['user_id'],
        appointment_id=data['appointment_id'],
        amount=data['amount'],
        payment_method=data['payment_method'],
        payment_reference=payment_reference,
        status='pending'
    )
    
    db.session.add(payment)
    db.session.commit()
    
    return jsonify({
        'message': 'Payment created successfully',
        'payment_id': payment.id,
        'payment_reference': payment_reference,
        'amount': payment.amount
    }), 201

@app.route('/payments', methods=['GET'])
def get_payments():
    user_id = request.args.get('user_id')
    
    if user_id:
        payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all() # Ditambahkan .order_by(Payment.created_at.desc())
    else:
        payments = Payment.query.order_by(Payment.created_at.desc()).all() # Ditambahkan .order_by(Payment.created_at.desc())
    
    result = []
    for payment in payments:
        result.append({
            'id': payment.id,
            'user_id': payment.user_id,
            'appointment_id': payment.appointment_id,
            'amount': payment.amount,
            'payment_method': payment.payment_method,
            'payment_reference': payment.payment_reference,
            'status': payment.status,
            'created_at': payment.created_at.isoformat()
        })
    
    return jsonify(result)

@app.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    return jsonify({
        'id': payment.id,
        'user_id': payment.user_id,
        'appointment_id': payment.appointment_id,
        'amount': payment.amount,
        'payment_method': payment.payment_method,
        'payment_reference': payment.payment_reference,
        'status': payment.status,
        'created_at': payment.created_at.isoformat()
    })

@app.route('/payments/<int:payment_id>/status', methods=['PUT'])
def update_payment_status(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'message': 'Status is required'}), 400

    # Logic to prevent changing from 'completed' to 'failed'
    if payment.status == 'completed' and new_status == 'failed':
        return jsonify({'message': 'Cannot change status from completed to failed'}), 400
        
    old_status = payment.status
    payment.status = new_status
    
    if new_status == 'completed' and old_status != 'completed':
        payment.paid_at = datetime.utcnow()
        
        # Update appointment status
        try:
            response = requests.post(
                f'{APPOINTMENT_SERVICE_URL}/appointments/{payment.appointment_id}/confirm-payment'
            )
            # You might want to handle response status from appointment service here
        except requests.exceptions.RequestException as e:
            # Log the error but allow payment status update to proceed
            print(f"Error updating appointment status for payment {payment_id}: {e}")
            pass  # Continue even if appointment service is unavailable
    
    db.session.commit()
    
    return jsonify({'message': 'Payment status updated successfully'})

@app.route('/payments/<int:payment_id>/confirm', methods=['POST'])
def confirm_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.status != 'pending':
        return jsonify({'message': 'Payment is not in pending status'}), 400
    
    payment.status = 'completed'
    payment.paid_at = datetime.utcnow()
    
    # Update appointment status
    try:
        response = requests.post(
            f'{APPOINTMENT_SERVICE_URL}/appointments/{payment.appointment_id}/confirm-payment'
        )
    except requests.exceptions.RequestException:
        pass  # Continue even if appointment service is unavailable
    
    db.session.commit()
    
    return jsonify({
        'message': 'Payment confirmed successfully',
        'payment_reference': payment.payment_reference
    })

@app.route('/payments/appointment/<int:appointment_id>', methods=['GET'])
def get_payment_by_appointment(appointment_id):
    payment = Payment.query.filter_by(appointment_id=appointment_id).first()
    
    if not payment:
        return jsonify({'message': 'Payment not found'}), 404
    
    return jsonify({
        'id': payment.id,
        'user_id': payment.user_id,
        'appointment_id': payment.appointment_id,
        'amount': payment.amount,
        'payment_method': payment.payment_method,
        'payment_reference': payment.payment_reference,
        'status': payment.status,
        'created_at': payment.created_at.isoformat(),
        'paid_at': payment.paid_at.isoformat() if payment.paid_at else None
    })

if __name__ == '__main__':
    app.run(debug=True, port=5004)