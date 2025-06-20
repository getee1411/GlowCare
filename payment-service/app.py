from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import uuid
import os
from model import db, Payment

app = Flask(__name__)
CORS(app)

# Configure database
db_path = os.path.join(os.path.dirname(__file__), 'payments.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

APPOINTMENT_SERVICE_URL = 'http://localhost:5002'

with app.app_context():
    try:
        db.create_all()
        print("✅ Payment database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'payment-service',
        'database': 'connected'
    }), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'GlowCare Payment Service',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'payments': '/payments (GET/POST)',
            'payment': '/payments/<id> (GET)',
            'status': '/payments/<id>/status (PUT)',
            'confirm': '/payments/<id>/confirm (POST)',
            'by_appointment': '/payments/appointment/<id> (GET)'
        }
    }), 200

@app.route('/payments', methods=['POST'])
def create_payment():
    try:
        data = request.get_json()
        print(f"=== CREATE PAYMENT ===")
        print(f"Received payment data: {data}")
        
        if not data:
            print("❌ No data provided")
            return jsonify({'message': 'No data provided'}), 400
            
        required_fields = ['user_id', 'appointment_id', 'amount', 'payment_method']
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing field: {field}")
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # Validate data types
        try:
            user_id = int(data['user_id'])
            appointment_id = int(data['appointment_id'])
            amount = int(data['amount'])
        except ValueError as e:
            print(f"❌ Invalid data type: {e}")
            return jsonify({'message': 'Invalid data types. user_id, appointment_id, and amount must be integers'}), 400
        
        # Check if payment already exists for this appointment
        existing_payment = Payment.query.filter_by(appointment_id=appointment_id).first()
        if existing_payment:
            print(f"❌ Payment already exists for appointment {appointment_id}")
            return jsonify({
                'message': f'Payment already exists for appointment {appointment_id}',
                'existing_payment_id': existing_payment.id,
                'payment_reference': existing_payment.payment_reference
            }), 409
        
        # Generate unique payment reference
        payment_reference = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
        
        print(f"Creating payment with reference: {payment_reference}")
        
        payment = Payment(
            user_id=user_id,
            appointment_id=appointment_id,
            amount=amount,
            payment_method=data['payment_method'].strip(),
            payment_reference=payment_reference,
            status='pending'
        )
        
        db.session.add(payment)
        db.session.commit()
        
        print(f"✅ Payment created successfully: ID={payment.id}, Reference={payment.payment_reference}")
        
        return jsonify({
            'success': True,
            'message': f'Payment created successfully! Reference: {payment.payment_reference}',
            'payment': {
                'id': payment.id,
                'payment_reference': payment.payment_reference,
                'user_id': payment.user_id,
                'appointment_id': payment.appointment_id,
                'amount': payment.amount,
                'payment_method': payment.payment_method,
                'status': payment.status,
                'created_at': payment.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating payment: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to create payment: {str(e)}'
        }), 500

@app.route('/payments', methods=['GET'])
def get_payments():
    try:
        user_id = request.args.get('user_id')
        print(f"=== GET PAYMENTS ===")
        print(f"Requested user_id: {user_id}")
        
        if user_id:
            payments = Payment.query.filter_by(user_id=int(user_id)).order_by(Payment.created_at.desc()).all()
            print(f"Found {len(payments)} payments for user {user_id}")
        else:
            payments = Payment.query.order_by(Payment.created_at.desc()).all()
            print(f"Found {len(payments)} total payments")
        
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
                'created_at': payment.created_at.isoformat(),
                'paid_at': payment.paid_at.isoformat() if payment.paid_at else None
            })
        
        print(f"Returning {len(result)} payments")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error fetching payments: {str(e)}")
        return jsonify({'message': f'Failed to fetch payments: {str(e)}'}), 500

@app.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)
        
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
        
    except Exception as e:
        print(f"❌ Error fetching payment: {str(e)}")
        return jsonify({'message': 'Payment not found'}), 404

@app.route('/payments/<int:payment_id>/status', methods=['PUT'])
def update_payment_status(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'message': 'Status field required'}), 400
        
        old_status = payment.status
        payment.status = data['status']
        
        if data['status'] == 'completed' and old_status != 'completed':
            payment.paid_at = datetime.utcnow()
        
        db.session.commit()
        
        print(f"✅ Payment {payment_id} status updated from {old_status} to {payment.status}")
        
        return jsonify({
            'message': 'Payment status updated successfully',
            'payment_id': payment.id,
            'old_status': old_status,
            'new_status': payment.status
        })
        
    except Exception as e:
        print(f"❌ Error updating payment status: {str(e)}")
        db.session.rollback()
        return jsonify({'message': f'Failed to update payment status: {str(e)}'}), 500

@app.route('/payments/<int:payment_id>/confirm', methods=['POST'])
def confirm_payment(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        if payment.status == 'completed':
            return jsonify({'message': 'Payment is already completed'}), 400
        
        payment.status = 'completed'
        payment.paid_at = datetime.utcnow()
        
        db.session.commit()
        
        print(f"✅ Payment {payment_id} confirmed successfully")
        
        return jsonify({
            'message': 'Payment confirmed successfully',
            'payment_reference': payment.payment_reference,
            'paid_at': payment.paid_at.isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error confirming payment: {str(e)}")
        db.session.rollback()
        return jsonify({'message': f'Failed to confirm payment: {str(e)}'}), 500

@app.route('/payments/appointment/<int:appointment_id>', methods=['GET'])
def get_payment_by_appointment(appointment_id):
    try:
        payment = Payment.query.filter_by(appointment_id=appointment_id).first()
        
        if not payment:
            return jsonify({'message': 'No payment found for this appointment'}), 404
        
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
        
    except Exception as e:
        print(f"❌ Error fetching payment by appointment: {str(e)}")
        return jsonify({'message': 'Failed to fetch payment'}), 500

if __name__ == '__main__':
    print("🚀 Starting Payment Service...")
    print(f"Database path: {db_path}")
    app.run(debug=True, port=5004, host='0.0.0.0')