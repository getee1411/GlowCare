from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from model import db, Treatment

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///treatments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

APPOINTMENT_SERVICE_URL = 'http://localhost:5002'

with app.app_context():
    db.create_all()
    # Add default treatments if none exist
    if not Treatment.query.first():
        default_treatments = [
            Treatment(name='Facial Treatment', description='Deep cleansing and moisturizing facial', price=150000, duration=60),
            Treatment(name='Body Massage', description='Relaxing full body massage', price=200000, duration=90),
            Treatment(name='Hair Treatment', description='Nourishing hair mask and styling', price=100000, duration=45),
            Treatment(name='Manicure & Pedicure', description='Complete nail care and polish', price=80000, duration=60),
            Treatment(name='Body Scrub', description='Exfoliating body treatment', price=120000, duration=45)
        ]
        for treatment in default_treatments:
            db.session.add(treatment)
        db.session.commit()
        print("Default treatments added to database")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'treatment-service'}), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'GlowCare Treatment Service',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'treatments': '/treatments (GET/POST)',
            'treatment': '/treatments/<id> (GET/PUT/DELETE)',
            'book': '/treatments/<id>/book (POST)'
        }
    }), 200

@app.route('/treatments', methods=['GET'])
def get_treatments():
    try:
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
    except Exception as e:
        print(f"Error fetching treatments: {str(e)}")
        return jsonify({'message': 'Failed to fetch treatments'}), 500

@app.route('/treatments/<int:treatment_id>', methods=['GET'])
def get_treatment(treatment_id):
    try:
        treatment = Treatment.query.get_or_404(treatment_id)
        return jsonify({
            'id': treatment.id,
            'name': treatment.name,
            'description': treatment.description,
            'price': treatment.price,
            'duration': treatment.duration,
            'created_at': treatment.created_at.isoformat()
        })
    except Exception as e:
        print(f"Error fetching treatment: {str(e)}")
        return jsonify({'message': 'Treatment not found'}), 404

@app.route('/treatments', methods=['POST'])
def create_treatment():
    try:
        data = request.get_json()
        print(f"Received treatment data: {data}")
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        required_fields = ['name', 'price', 'duration']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        treatment = Treatment(
            name=data['name'],
            description=data.get('description', ''),
            price=int(data['price']),
            duration=int(data['duration'])
        )
        
        db.session.add(treatment)
        db.session.commit()
        
        return jsonify({
            'message': 'Treatment created successfully',
            'treatment_id': treatment.id
        }), 201
        
    except Exception as e:
        print(f"Error creating treatment: {str(e)}")
        db.session.rollback()
        return jsonify({'message': f'Failed to create treatment: {str(e)}'}), 500

@app.route('/treatments/<int:treatment_id>', methods=['PUT'])
def update_treatment(treatment_id):
    try:
        treatment = Treatment.query.get_or_404(treatment_id)
        data = request.get_json()
        
        if 'name' in data:
            treatment.name = data['name']
        if 'description' in data:
            treatment.description = data['description']
        if 'price' in data:
            treatment.price = int(data['price'])
        if 'duration' in data:
            treatment.duration = int(data['duration'])
        
        db.session.commit()
        return jsonify({'message': 'Treatment updated successfully'})
        
    except Exception as e:
        print(f"Error updating treatment: {str(e)}")
        db.session.rollback()
        return jsonify({'message': f'Failed to update treatment: {str(e)}'}), 500

@app.route('/treatments/<int:treatment_id>', methods=['DELETE'])
def delete_treatment(treatment_id):
    try:
        treatment = Treatment.query.get_or_404(treatment_id)
        db.session.delete(treatment)
        db.session.commit()
        
        return jsonify({'message': 'Treatment deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting treatment: {str(e)}")
        db.session.rollback()
        return jsonify({'message': f'Failed to delete treatment: {str(e)}'}), 500

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