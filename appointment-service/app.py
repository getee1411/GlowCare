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

@app.route('/appointments', methods=['POST'])
def create_appointment():
    data = request.get_json()
    
    appointment = Appointment(
        user_id=data['user_id'],
        treatment_id=data['treatment_id'],
        appointment_date=datetime.strptime(data['appointment_date'], '%Y-%m-%d %H:%M'),
        status='pending'
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment created successfully',
        'appointment_id': appointment.id
    }), 201

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