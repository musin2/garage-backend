#!/usr/bin/env python3

from app import app
from models import db, User, Vehicle, Service, Appointment, ServiceVehicle, Mechanic
from datetime import datetime
from werkzeug.security import generate_password_hash

with app.app_context():

    # This will delete any existing rows so you can run the seed file multiple times without having duplicate entries
    print("Deleting data...")
    Appointment.query.delete()
    ServiceVehicle.query.delete()
    Vehicle.query.delete()
    Service.query.delete()
    User.query.delete()
    Mechanic.query.delete()

    # Creating users with roles and hashed passwords
    print("Creating users...")
    alice = User(
        name="Alice Johnson", 
        email="alice@example.com", 
        phone_number="1234567890", 
        password=generate_password_hash("pass123"),  # Hash the password
        role="admin"
    )
    bob = User(
        name="Bob Smith", 
        email="bob@example.com", 
        phone_number="0987654321", 
        password=generate_password_hash("123123"),  # Hash the password
        role="customer"
    )
    users = [alice, bob]

    # Creating vehicles for users
    print("Creating vehicles...")
    vehicle1 = Vehicle(make="Toyota", model="Corolla", year=2019, license_plate="ABC123", owner=alice)
    vehicle2 = Vehicle(make="Honda", model="Civic", year=2021, license_plate="XYZ987", owner=bob)
    vehicles = [vehicle1, vehicle2]

    # Creating services
    print("Creating services...")
    oil_change = Service(service_name="Oil Change", description="Basic engine oil change", price=50.00)
    tire_rotation = Service(service_name="Tire Rotation", description="Tire rotation for even wear", price=30.00)
    brake_inspection = Service(service_name="Brake Inspection", description="Comprehensive brake system check", price=70.00)
    services = [oil_change, tire_rotation, brake_inspection]

    # Creating mechanics
    print("Creating mechanics...")
    mechanic1 = Mechanic(name="John Doe", phone_number="5551234567")
    mechanic2 = Mechanic(name="Jane Smith", phone_number="5557654321")
    mechanics = [mechanic1, mechanic2]

    # Associating services with vehicles (Many-to-Many)
    print("Creating service-vehicle associations...")
    sv1 = ServiceVehicle(vehicle=vehicle1, service=oil_change)
    sv2 = ServiceVehicle(vehicle=vehicle2, service=tire_rotation)
    service_vehicles = [sv1, sv2]

    # Creating appointments for users and vehicles
    print("Creating appointments...")
    appointment1 = Appointment(user=alice, vehicle=vehicle1, service_date=datetime(2024, 10, 20, 9, 0, 0), status="scheduled", mechanic=mechanic1)
    appointment2 = Appointment(user=bob, vehicle=vehicle2, service_date=datetime(2024, 10, 22, 14, 0, 0), status="scheduled", mechanic=mechanic2)
    appointments = [appointment1, appointment2]

    # Adding everything to the database
    print("Adding data to the database...")
    db.session.add_all(users)
    db.session.add_all(vehicles)
    db.session.add_all(services)
    db.session.add_all(mechanics)
    db.session.add_all(service_vehicles)
    db.session.add_all(appointments)
    db.session.commit()

    print("Seeding done!")
