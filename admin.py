import random
import string
from flask import Blueprint, jsonify, request
from peewee import Model, CharField, DateTimeField, AutoField
from db_config import db
from datetime import datetime
from peewee import IntegrityError, DoesNotExist
from werkzeug.security import generate_password_hash, check_password_hash


admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')

class BaseModel(Model):
    """
    Base model that defines the database for all models.
    """
    class Meta:
        database = db

class Admin(BaseModel):
    admin_id = AutoField()
    email = CharField(unique=True)
    password = CharField(max_length=255)
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    role = CharField(max_length=255) # super admin, admin
    created_at = DateTimeField(default=lambda: datetime.now())

    class Meta:
        table_name = 'Admin'

with db.connection_context():
        db.create_tables([Admin])

# keep this route disabled once the admin is registered, will be used in future 
@admin_blueprint.route('/register', methods=['POST']) 
def register_admin():
    """
    API endpoint to register admin in the database.
    TODO role should not be the input, only SU can change role
    """
    try:
        data = request.get_json()

        # Input Validation
        required_fields = ["email", "password", "first_name", "last_name", "role"]
        if not all(key in data for key in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        data["password"] = generate_password_hash(data["password"])

        with db.connection_context():
            admin = Admin.create(**data)

        return jsonify({
            'message': 'Admin registered successfully!',
            'admin': {
                'admin_id': admin.admin_id,
                'email': admin.email,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'role': admin.role,
                'created_at': admin.created_at
            }
        }), 201

    except IntegrityError:
        return jsonify({"error": "Admin with this email already exists!"}), 409
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    

@admin_blueprint.route('/login', methods=['POST'])
def login_admin():
    """
    API endpoint for admin login.
    """
    try:
        data = request.get_json()

        # Validate Input
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email and password are required"}), 400
        
        email = data.get('email')
        password = data.get('password')

        with db.connection_context():
            try:
                admin = Admin.get(Admin.email == email)
            except DoesNotExist:
                return jsonify({"message": "Invalid credentials"}), 401

        if not admin or not check_password_hash(admin.password, password):
            return jsonify({"message": "Invalid credentials"}), 401
        
        return jsonify({
            'message': 'login successful!',
            'admin': {
                'email': admin.email,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'role': admin.role
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@admin_blueprint.route('/profile', methods=['POST'])
def profile():
    try:
        data = request.get_json()

        email = data.get('email')

        if email:  # Fetch a specific user’s profile
            with db.connection_context():
                admin = Admin.get_or_none(Admin.email == email)
            
            if not admin:
                return jsonify({"error": "User not found"}), 404
        else:
            return jsonify({"error": "email not found"}), 404

        return jsonify({
            'email': admin.email,
            'first_name': admin.first_name,
            'last_name': admin.last_name,
            'role': admin.role
        }), 200

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

    
# keep this route disabled in production for now, will be used in future
@admin_blueprint.route('/delete', methods=['DELETE'])
def delete_admin():
    """
    API endpoint to delete an admin.
    """
    try:
        data = request.get_json()

        # Validate Input
        if not data or 'email' not in data:
            return jsonify({"error": "Email is required"}), 400
        
        email = data['email']
        
        with db.connection_context():
            admin = Admin.get_or_none(Admin.email == email)
            if not admin:
                return jsonify({"message": "Invalid email"}), 404

            admin.delete_instance()
        
        return jsonify({'message': 'Admin deleted successfully!'}), 200

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@admin_blueprint.route('/change-password', methods=['POST'])
def change_password():
    """
    API endpoint to change admin password 
    """
    try:
        data = request.get_json()

        # Validate Input
        if not data or 'email' not in data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({"error": "Email, current password and new password is required"}), 400
        
        email = data['email']
        current_password = data['current_password']
        new_password = generate_password_hash(data['new_password'])

        with db.connection_context():
            try:
                admin = Admin.get(Admin.email == email)
            except DoesNotExist:
                return jsonify({"message": "Invalid email or current password"}), 401

        if not admin or not check_password_hash(admin.password, current_password):
            return jsonify({"message": "Invalid email or current password"}), 401
        
        admin.password = new_password
        admin.save()

        return jsonify({'message': 'password updated successfully!'}), 200
    
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    

@admin_blueprint.route('/recover-password', methods=['POST'])
def recover_password():
    try:
        from utils import send_email
        
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        with db.connection_context():
            admin = Admin.get_or_none(Admin.email == email)

        if not admin:
            return jsonify({"error": "Amin not found"}), 404

        # Generate a random 12-character password
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        print(new_password)

        # Hash the password before storing
        hashed_password = generate_password_hash(new_password)

        with db.connection_context():
            admin.password = hashed_password
            admin.save()

        # Send email with the new password
        send_email(
            subject="Password Reset",
            recipients=[email],
            body=f"Your new password is: {new_password}\nPlease change it after logging in."
        )

        return jsonify({"message": "New password sent to your email"}), 200

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500