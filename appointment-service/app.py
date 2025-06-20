from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from model import db, Appointment

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appointments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'appointment-service'}), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'GlowCare Appointment Service',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'appointments': '/appointments (GET/POST)',
            'appointment': '/appointments/<id> (GET/PUT/DELETE)',
            'cancel': '/appointments/<id>/cancel (POST)',
            'confirm_payment': '/appointments/<id>/confirm-payment (POST)'
        }
    }), 200

@app.route('/appointments', methods=['POST'])
def create_appointment():
    try:
        data = request.get_json()
        print(f"=== CREATE APPOINTMENT ===")
        print(f"Received data: {data}")
        
        # Validate required fields
        if not data:
            print("❌ No data provided")
            return jsonify({'message': 'No data provided'}), 400
            
        required_fields = ['user_id', 'treatment_id', 'appointment_date']
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing field: {field}")
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # Parse datetime
        appointment_date_str = data['appointment_date']
        try:
            if 'T' in appointment_date_str:
                appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%dT%H:%M')
            else:
                appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d %H:%M')
        except ValueError as e:
            print(f"❌ Date parsing error: {e}")
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD HH:MM or YYYY-MM-DDTHH:MM'}), 400
        
        # Create appointment
        appointment = Appointment(
            user_id=int(data['user_id']),
            treatment_id=int(data['treatment_id']),
            appointment_date=appointment_date,
            status='pending'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        print(f"✅ Appointment created successfully: ID={appointment.id}, User={appointment.user_id}, Treatment={appointment.treatment_id}")
        
        # Enhanced response with all details
        return jsonify({
            'success': True,
            'message': f'Appointment created successfully! Your appointment ID is #{appointment.id}',
            'appointment': {
                'id': appointment.id,
                'user_id': appointment.user_id,
                'treatment_id': appointment.treatment_id,
                'appointment_date': appointment.appointment_date.isoformat(),
                'status': appointment.status,
                'created_at': appointment.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating appointment: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to create appointment: {str(e)}'
        }), 500

@app.route('/appointments', methods=['GET'])
def get_appointments():
    user_id = request.args.get('user_id')
    
    if user_id:
        appointments = Appointment.query.filter_by(user_id=user_id).all()
    else:
        appointments = Appointment.query.all()
    
    result = []
    for appointment in appointments:
        result.append({
            'id': appointment.id,
            'user_id': appointment.user_id,
            'treatment_id': appointment.treatment_id,
            'appointment_date': appointment.appointment_date.isoformat(),
            'status': appointment.status,
            'created_at': appointment.created_at.isoformat()
        })
    
    return jsonify(result)

@app.route('/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    return jsonify({
        'id': appointment.id,
        'user_id': appointment.user_id,
        'treatment_id': appointment.treatment_id,
        'appointment_date': appointment.appointment_date.isoformat(),
        'status': appointment.status,
        'created_at': appointment.created_at.isoformat()
    })

@app.route('/appointments/<int:appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    data = request.get_json()
    
    if 'appointment_date' in data:
        appointment.appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d %H:%M')
    
    if 'status' in data:
        appointment.status = data['status']
    
    if 'treatment_id' in data:
        appointment.treatment_id = data['treatment_id']
    
    db.session.commit()
    
    return jsonify({'message': 'Appointment updated successfully'})

@app.route('/appointments/<int:appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    db.session.delete(appointment)
    db.session.commit()
    
    return jsonify({'message': 'Appointment deleted successfully'})

@app.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = 'cancelled'
    
    db.session.commit()
    
    return jsonify({'message': 'Appointment cancelled successfully'})

@app.route('/appointments/<int:appointment_id>/confirm-payment', methods=['POST'])
def confirm_payment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = 'paid'
    
    db.session.commit()
    
    return jsonify({'message': 'Payment confirmed for appointment'})

if __name__ == '__main__':
    app.run(debug=True, port=5002)