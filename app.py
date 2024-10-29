from flask import Flask, request, make_response, jsonify, session
from flask_session import Session
from models import db, User, Vehicle, Service, Appointment
from flask import Flask, request, make_response, jsonify
from models import db, User, Vehicle, Service, Appointment,Mechanic
from datetime import datetime,timedelta
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import json
from functools import wraps
from flask_cors import CORS
from flask import jsonify

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False
app.config['SECRET_KEY'] = 'secret_key'
app.config['SESSION_TYPE'] = 'filesystem'




login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)
db.init_app(app)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            print(session)
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User Registration
from flask import make_response  # Import make_response
from werkzeug.security import generate_password_hash  # Ensure this is imported

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        hashed_password = generate_password_hash(data['password'])

        new_user = User(
            name=data['name'], 
            email=data['email'], 
            phone_number=data['phone_number'],
            password=hashed_password,
            role=data['role']
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Store user data in the session (optional)
        session['user_id'] = new_user.id
        session['role'] = new_user.role
        session['name'] = new_user.name
        session['phone_number'] = new_user.phone_number
        session['email'] = new_user.email
        
        # Create a response object
        response = make_response(jsonify({
            "message": "User registered successfully!", 
            "id": new_user.id,
            "name": new_user.name,
            "phone_number": new_user.phone_number,
            "role": new_user.role,
            "email": new_user.email
        }), 201)

        # Set cookies
        response.set_cookie("user_id", str(new_user.id), httponly=True, expires=7 * 24 * 60 * 60)  # 7 days
        response.set_cookie("user_name", new_user.name, httponly=True, expires=7 * 24 * 60 * 60)
        response.set_cookie("user_email", new_user.email, httponly=True, expires=7 * 24 * 60 * 60)
        response.set_cookie("user_phone", new_user.phone_number, httponly=True, expires=7 * 24 * 60 * 60)
        response.set_cookie("user_role", new_user.role, httponly=True, expires=7 * 24 * 60 * 60)

        return response  # Return the response object with cookies

    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500

    
@app.route('/session', methods=['GET'])
def get_session():
    return jsonify(session), 200

    
# User Login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password, password):
        # Store user info in session
        session['user_id'] = user.id
        session['name'] = user.name
        session['role'] = user.role
        session['phone_number'] = user.phone_number
        session['email'] = user.email
        
        print("Session after login:", session)
        
        # Create a response object to set cookies
        response = make_response(jsonify({
            "message": "Login successful", 
            "id": user.id,
            "name": user.name,
            "phone_number": user.phone_number,
            "role": user.role,
            "email": user.email
        }), 200)
                
        return response
    
    return jsonify({"error": "Invalid credentials"}), 401



@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    response = make_response(jsonify({"message": "Logged out successfully!"}), 200)
    response.set_cookie('session', '', expires=0) 
    
    return response

@app.route('/get-role', methods=['GET'])
def get_role():
    # Check if the user is logged in via session (or token if you’re using that)
    user_id = session.get('user_id')  # Assuming you store user ID in session on login

    if not user_id:
        return jsonify({'error': 'No user logged in'}), 401

    # Query the user from the database
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Return the user's role
    return jsonify({'role': user.role}), 200

# @app.route("/users")
# def get_users():
#     users=User.query.all()
#     return users

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    users_dict=[user.to_dict() for user in users]
    # service_data = [{'id': s.id, 'service_name': s.service_name, 'description': s.description, 'price': str(s.price)} for s in services]
    
    return make_response(users_dict, 200)


@app.route('/users/<int:user_id>', methods=['PATCH'])
def update_user(user_id):
    # Fetch the user by id
    user = User.query.get_or_404(user_id)

    # Get the updated data from the request
    data = request.get_json()

    # Update the user's details
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        user.email = data['email']
    if 'phone_number' in data:
        user.phone_number = data['phone_number']

    # Commit the changes to the database
    try:
        db.session.commit()
        return jsonify({"message": "User updated successfully", "user": user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/')
def index():
    return make_response('<h1>Garage routes</h1>', 200)

# Manage Vehicle Information
@app.route('/users/<int:user_id>/vehicles', methods=['POST'])
def add_vehicle(user_id):
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    new_vehicle = Vehicle(
        make=data['make'], 
        model=data['model'], 
        year=data['year'], 
        license_plate=data['vehicle_plate'],
        owner=user
    )
    db.session.add(new_vehicle)
    db.session.commit()

    response_body = {
        'message': 'Vehicle added successfully!',
        'id': new_vehicle.id  # Return the newly created vehicle's ID
    }
    return make_response(json.dumps(response_body), 201)

@app.route('/users/<int:user_id>/vehicles/<int:license_plate>', methods=['PATCH'])
def update_vehicle(user_id, license_plate):
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    vehicle = Vehicle.query.get_or_404(license_plate)

    # Check if the vehicle belongs to the user
    if vehicle.owner != user:
        return make_response(json.dumps({'message': 'Vehicle not found for this user'}), 404)

    # Update the vehicle's attributes if they are provided
    if 'make' in data:
        vehicle.make = data['make']
    if 'model' in data:
        vehicle.model = data['model']
    if 'year' in data:
        vehicle.year = data['year']
    if 'license_plate' in data:
        vehicle.license_plate = data['license_plate']

    db.session.commit()

    response_body = {
        'message': 'Vehicle updated successfully!',
        'vehicle': {
            'make': vehicle.make,
            'model': vehicle.model,
            'year': vehicle.year,
            'license_plate': vehicle.license_plate,
            'owner': user.id  # Include the owner's ID for reference
        }
    }
    return make_response(json.dumps(response_body), 200)


@app.route('/users/<int:user_id>/vehicles', methods=['GET'])
def get_user_vehicles(user_id):
    user = User.query.get_or_404(user_id)
    vehicles = Vehicle.query.filter_by(user_id=user.id).all()
    vehicle_data = [{'id': v.id, 'make': v.make, 'model': v.model, 'year': v.year, "license_plate": v.license_plate} for v in vehicles]

    return make_response(json.dumps(vehicle_data), 200)


# View List of Services Offered by the Garage
@app.route('/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    service_data = [{'id': s.id, 'service_name': s.service_name, 'description': s.description, 'price': str(s.price)} for s in services]
    
    return make_response(json.dumps(service_data), 200)

# Garage Owner: Manage Services

@app.route('/services', methods=['POST'])
# @admin_required
def add_service():
    data = request.get_json()
    new_service = Service(
        service_name=data['service_name'], 
        description=data['description'], 
        price=data['price']
    )
    db.session.add(new_service)
    db.session.commit()

    response_body = {
        'message': 'Service added successfully!'
    }
    return make_response(json.dumps(response_body), 201)


@app.route('/services/<int:service_id>', methods=['PATCH'])
# @admin_required
def update_service(service_id):
    service = Service.query.get_or_404(service_id)
    data = request.get_json()

    service.service_name = data.get('service_name', service.service_name)
    service.description = data.get('description', service.description)
    service.price = data.get('price', service.price)

    db.session.commit()

    response_body = {
        'message': 'Service updated successfully!'
    }
    return make_response(json.dumps(response_body), 200)


@app.route('/services/<int:service_id>', methods=['DELETE'])
# @admin_required
def delete_service(service_id):
    print("Current Session on DELETE request:", session)
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()

    response_body = {
        'message': 'Service deleted successfully!'
    }
    return make_response(json.dumps(response_body), 200)

# Garage Owner: View Customer Requests


from flask import jsonify, request
from datetime import datetime

@app.route('/appointments', methods=['GET'])
def view_appointments():
    appointments = Appointment.query.all()
    response_body = [a.to_dict() for a in appointments]
    return jsonify(response_body), 200


# Schedule Service Appointment
@app.route('/appointments', methods=['POST'])
def schedule_appointment():
    data = request.get_json()

    user_id = data.get('user_id')
    license_plate = data.get('vehicle_plate')
    service_date_str = data.get('service_date')
    mechanic_id = data.get('mechanic_id')

    if not (user_id and license_plate and service_date_str and mechanic_id):
        return jsonify({"error": "Missing required data: 'user_id', 'license_plate', 'service_date', and 'mechanic_id'"}), 400

    try:
        service_date = datetime.strptime(service_date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return jsonify({"error": "Invalid date format. Expected 'YYYY-MM-DD HH:MM:SS'"}), 400

    status = 'scheduled'

    # Check if user and vehicle exist
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": f"User with ID {user_id} does not exist."}), 404

    vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
    if vehicle is None:
        return jsonify({"error": f"Vehicle with License Plate {license_plate} does not exist."}), 404

    mechanic = Mechanic.query.get(mechanic_id)
    if mechanic is None:
        return jsonify({"error": f"Mechanic with ID {mechanic_id} does not exist."}), 404

    new_appointment = Appointment(
        user=user,
        vehicle=vehicle,
        service_date=service_date,
        status=status,
        mechanic=mechanic
    )

    try:
        db.session.add(new_appointment)
        db.session.commit()
        return jsonify({
            'message': 'Appointment scheduled successfully!',
            'appointment': new_appointment.to_dict()  # Return appointment details
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Could not schedule appointment. Please try again later."}), 500

@app.route('/appointments/<int:appointment_id>', methods=['PATCH'])
# @admin_required
def update_appointment_status(appointment_id):
    # Fetch the appointment by ID
    appointment = Appointment.query.get_or_404(appointment_id)

    # Get the new status from the request body
    data = request.get_json()
    new_status = data.get('status')

    # Validate the status
    valid_statuses = ['complete', 'ongoing', 'scheduled']
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Allowed values are: {valid_statuses}"}), 400

    # Update the status
    appointment.status = new_status

    try:
        db.session.commit()
        return jsonify({'message': f'Appointment {appointment_id} updated to status: {new_status}!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Could not update appointment status."}), 500
    


@app.route("/mechanics", methods=["GET"])
def get_all_mechanics():
    mechanics = Mechanic.query.all()
    return jsonify([mechanic.to_dict() for mechanic in mechanics]), 200

@app.route("/mechanics/<int:id>", methods=["GET"])
def get_mechanic_by_id(id):
    mechanic = Mechanic.query.get(id)
    if mechanic is None:
        return jsonify({"error": "Mechanic not found"}), 404
    return jsonify(mechanic.to_dict()), 200

@app.route("/mechanics", methods=["POST"])
def create_mechanic():
    data = request.json
    if not data or 'name' not in data or 'phone_number' not in data:
        return jsonify({"error": "Name and phone number are required"}), 400

    new_mechanic = Mechanic(
        name=data['name'],
        phone_number=data['phone_number']
    )
    db.session.add(new_mechanic)
    db.session.commit()

    return jsonify(new_mechanic.to_dict()), 201





if __name__ == '__main__':
    app.run()
