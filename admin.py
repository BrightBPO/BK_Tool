from flask import Blueprint, jsonify, request, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from peewee import Model, CharField, DateTimeField, AutoField
from db_config import db
from datetime import datetime
from peewee import IntegrityError, DoesNotExist
from werkzeug.security import generate_password_hash, check_password_hash

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')

login_manager = LoginManager()

class BaseModel(Model):
    """
    Base model that defines the database for all models.
    """
    class Meta:
        database = db

class Admin(UserMixin, BaseModel):
    admin_id = AutoField()
    email = CharField(unique=True)
    password = CharField(max_length=255)
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    role = CharField(max_length=255) # super admin, admin
    created_at = DateTimeField(default=lambda: datetime.now())

    class Meta:
        table_name = 'Admin'

    def get_id(self):
        return str(self.admin_id)  # Required for Flask-Login

with db.connection_context():
        db.create_tables([Admin])


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Unauthorized access. Please log in first."}), 401

@login_manager.user_loader
def load_user(admin_id):
    with db.connection_context():
        return Admin.get_or_none(Admin.admin_id == admin_id)

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
        
        email = data['email']
        password = data['password']
        
        with db.connection_context():
            try:
                admin = Admin.get(Admin.email == email)
            except DoesNotExist:
                return jsonify({"message": "Invalid email or password"}), 401

        if not admin or not check_password_hash(admin.password, password):
            return jsonify({"message": "Invalid email or password"}), 401
        
        login_user(admin)  # Maintain session
        session.modified = True  # Ensure Flask updates session state

        print("In login")
        
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
    

@admin_blueprint.route('/logout', methods=['POST'])
@login_required
def logout_admin():
    try:
        print("Before logout:", session)  # Print session data before clearing
        logout_user()
        session.clear()
        print("After logout:", session)  # Check if session is actually cleared
        
        return jsonify({'message': 'Logged out successfully'}), 200
    
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@admin_blueprint.route('/profile', methods=['GET'])
@login_required
def profile():
    try:
        return jsonify({
            'email': current_user.email,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'role': current_user.role
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    
# keep this route disabled in production for now, will be used in future
@admin_blueprint.route('/delete', methods=['POST'])
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

        session.clear()  # Clear session after deletion
        
        return jsonify({'message': 'Admin deleted successfully!'}), 200

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
