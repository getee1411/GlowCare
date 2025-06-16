from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
from model import db, Treatment

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///treatments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Service URLs
APPOINTMENT_SERVICE_URL = 'http://localhost:5002'

with app.app_context():
    db.create_all()
    # Insert sample treatments if none exist
    if not Treatment.query.first():
        sample_treatments = [
            Treatment(name='Facial Treatment', description='Deep cleansing facial treatment', price=150000, duration=60),
            Treatment(name='Hair Spa', description='Relaxing hair spa treatment', price=200000, duration=90),
            Treatment(name='Manicure & Pedicure', description='Complete nail care treatment', price=100000, duration=45),
            Treatment(name='Body Massage', description='Full body relaxation massage', price=300000, duration=120)
        ]
        for treatment in sample_treatments:
            db.session.add(treatment)
        db.session.commit()

@app.route('/treatments', methods=['GET'])
def get_treatments():
    treatments = Treatment.query.all()
    result = []
    
    for treatment in treatments:
        result.append({
            'id': treatment.id,
            'name': treatment.name,
            'description': treatment.description,
            'price': treatment.price,
            'duration': treatment.duration,
            'created_at': treatment.created_at.isoformat()
        })
    
    return jsonify(result)

@app.route('/treatments/<int:treatment_id>', methods=['GET'])
def get_treatment(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)
    
    return jsonify({
        'id': treatment.id,
        'name': treatment.name,
        'description': treatment.description,
        'price': treatment.price,
        'duration': treatment.duration,
        'created_at': treatment.created_at.isoformat()
    })

@app.route('/treatments', methods=['POST'])
def create_treatment():
    data = request.get_json()
    
    treatment = Treatment(
        name=data['name'],
        description=data.get('description', ''),
        price=data['price'],
        duration=data['duration']
    )
    
    db.session.add(treatment)
    db.session.commit()
    
    return jsonify({
        'message': 'Treatment created successfully',
        'treatment_id': treatment.id
    }), 201

@app.route('/treatments/<int:treatment_id>', methods=['PUT'])
def update_treatment(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)
    data = request.get_json()
    
    treatment.name = data.get('name', treatment.name)
    treatment.description = data.get('description', treatment.description)
    treatment.price = data.get('price', treatment.price)
    treatment.duration = data.get('duration', treatment.duration)
    
    db.session.commit()
    
    return jsonify({'message': 'Treatment updated successfully'})

@app.route('/treatments/<int:treatment_id>', methods=['DELETE'])
def delete_treatment(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)
    
    db.session.delete(treatment)
    db.session.commit()
    
    return jsonify({'message': 'Treatment deleted successfully'})

@app.route('/treatments/<int:treatment_id>/book', methods=['POST'])
def book_treatment(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)
    data = request.get_json()
    
    appointment_data = {
        'user_id': data['user_id'],
        'treatment_id': treatment_id,
        'appointment_date': data['appointment_date']
    }
    
    response = requests.post(f'{APPOINTMENT_SERVICE_URL}/appointments', json=appointment_data)
    
    if response.status_code == 201:
        return jsonify({
            'message': f'Appointment booked for {treatment.name}',
            'appointment_id': response.json()['appointment_id'],
            'treatment_price': treatment.price
        }), 201
    else:
        return jsonify({'message': 'Failed to book appointment'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5003)