from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import requests
from model import db, User
from flask_cors import CORS # Pastikan ini sudah ada

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'

db.init_app(app)
jwt = JWTManager(app)

# Service URLs
APPOINTMENT_SERVICE_URL = 'http://localhost:5002'
PAYMENT_SERVICE_URL = 'http://localhost:5004'

with app.app_context():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print(f"Received registration data: {data}") # Tambahkan ini

    if User.query.filter_by(email=data['email']).first():
        print(f"Email {data['email']} already exists.") # Tambahkan ini
        return jsonify({'message': 'Email already exists'}), 400

    selected_role = data.get('role', 'pasien')
    print(f"Role to be saved: {selected_role}") # Tambahkan ini

    user = User(
        name=data['name'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role=selected_role
    )

    db.session.add(user)
    db.session.commit()
    print(f"User {user.email} with role {user.role} registered successfully.") # Tambahkan ini

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user_id': user.id,
            'role': user.role
        }), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role
    })

@app.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    
    if 'password' in data:
        user.password_hash = generate_password_hash(data['password'])
    
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'})

@app.route('/book-appointment', methods=['POST'])
@jwt_required()
def book_appointment():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'pasien':
        return jsonify({'message': 'Only patients can book appointments'}), 403
    
    data = request.get_json()
    data['user_id'] = user_id
    
    response = requests.post(f'{APPOINTMENT_SERVICE_URL}/appointments', json=data)
    return jsonify(response.json()), response.status_code

@app.route('/make-payment', methods=['POST'])
@jwt_required()
def make_payment():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'pasien':
        return jsonify({'message': 'Only patients can make payments'}), 403
    
    data = request.get_json()
    data['user_id'] = user_id
    
    response = requests.post(f'{PAYMENT_SERVICE_URL}/payments', json=data)
    return jsonify(response.json()), response.status_code

@app.route('/appointments', methods=['GET'])
@jwt_required()
def view_appointments():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role in ['dokter', 'admin']:
        response = requests.get(f'{APPOINTMENT_SERVICE_URL}/appointments')
    else:
        response = requests.get(f'{APPOINTMENT_SERVICE_URL}/appointments?user_id={user_id}')
    
    return jsonify(response.json()), response.status_code

@app.route('/appointments/<int:appointment_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_appointment(appointment_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Only admin can manage appointments'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        response = requests.put(f'{APPOINTMENT_SERVICE_URL}/appointments/{appointment_id}', json=data)
    else:
        response = requests.delete(f'{APPOINTMENT_SERVICE_URL}/appointments/{appointment_id}')
    
    return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    app.run(debug=True, port=5001)