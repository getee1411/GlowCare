from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import requests
from model import db, User
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["*"])  # Allow all origins for development
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'

db.init_app(app)
jwt = JWTManager(app)

APPOINTMENT_SERVICE_URL = 'http://localhost:5002'
PAYMENT_SERVICE_URL = 'http://localhost:5004'

with app.app_context():
    db.create_all()

# Home endpoint
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'GlowCare User Service API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': 'GET /health',
            'register': 'POST /register',
            'login': 'POST /login',
            'profile': 'GET/PUT /profile (auth required)',
            'appointments': 'GET /appointments (auth required)',
            'book_appointment': 'POST /book-appointment (auth required)',
            'make_payment': 'POST /make-payment (auth required)'
        }
    }), 200

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print(f"Received registration data: {data}")

        # Validate required fields
        if not data or not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify({'message': 'Missing required fields'}), 400

        if User.query.filter_by(email=data['email']).first():
            print(f"Email {data['email']} already exists.")
            return jsonify({'message': 'Email already exists'}), 400

        selected_role = data.get('role', 'pasien')
        print(f"Role to be saved: {selected_role}")

        user = User(
            name=data['name'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role=selected_role
        )

        db.session.add(user)
        db.session.commit()
        print(f"User {user.email} with role {user.role} registered successfully.")

        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'message': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Missing email or password'}), 400
            
        user = User.query.filter_by(email=data['email']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'access_token': access_token,
                'user_id': user.id,
                'role': user.role,
                'name': user.name
            }), 200
        
        return jsonify({'message': 'Invalid credentials'}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'message': 'Login failed'}), 500

@app.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        })
    except Exception as e:
        print(f"Profile fetch error: {str(e)}")
        return jsonify({'message': 'Failed to fetch profile'}), 500

@app.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        data = request.get_json()
        
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        
        if 'password' in data and data['password']:
            user.password_hash = generate_password_hash(data['password'])
        
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'})
    except Exception as e:
        print(f"Profile update error: {str(e)}")
        return jsonify({'message': 'Failed to update profile'}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'user-service'}), 200

@app.route('/book-appointment', methods=['POST'])
@jwt_required()
def book_appointment():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'pasien':
            return jsonify({'message': 'Only patients can book appointments'}), 403
        
        data = request.get_json()
        data['user_id'] = user_id
        
        response = requests.post(f'{APPOINTMENT_SERVICE_URL}/appointments', json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Book appointment error: {str(e)}")
        return jsonify({'message': 'Failed to book appointment'}), 500

@app.route('/make-payment', methods=['POST'])
@jwt_required()
def make_payment():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'pasien':
            return jsonify({'message': 'Only patients can make payments'}), 403
        
        data = request.get_json()
        data['user_id'] = user_id
        
        response = requests.post(f'{PAYMENT_SERVICE_URL}/payments', json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Make payment error: {str(e)}")
        return jsonify({'message': 'Failed to make payment'}), 500

@app.route('/appointments', methods=['GET'])
@jwt_required()
def view_appointments():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        print(f"Fetching appointments for user {user_id} with role {user.role}")
        
        if user.role == 'pasien':
            # Patient can only see their own appointments
            url = f'{APPOINTMENT_SERVICE_URL}/appointments?user_id={user_id}'
        else:
            # Admin and doctors can see all appointments
            url = f'{APPOINTMENT_SERVICE_URL}/appointments'
        
        print(f"Making request to: {url}")
        response = requests.get(url)
        
        if response.status_code == 200:
            appointments = response.json()
            print(f"Retrieved {len(appointments)} appointments")
            return jsonify(appointments), 200
        else:
            print(f"Error from appointment service: {response.status_code}")
            return jsonify({'message': 'Failed to fetch appointments'}), response.status_code
        
    except Exception as e:
        print(f"View appointments error: {str(e)}")
        return jsonify({'message': 'Failed to fetch appointments'}), 500

@app.route('/appointments/<int:appointment_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_appointment(appointment_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role not in ['admin', 'pasien']:
            return jsonify({'message': 'Unauthorized'}), 403
        
        if request.method == 'PUT':
            data = request.get_json()
            response = requests.put(f'{APPOINTMENT_SERVICE_URL}/appointments/{appointment_id}', json=data)
        elif request.method == 'DELETE':
            response = requests.delete(f'{APPOINTMENT_SERVICE_URL}/appointments/{appointment_id}')
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Manage appointment error: {str(e)}")
        return jsonify({'message': 'Failed to manage appointment'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')