"""
Authentication server for JWT-based user signup, login, and dashboard access.
Handles user registration, authentication, and role-based access control.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import mysql.connector
import bcrypt
import jwt
import re
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# JWT Configuration
# Security configuration from environment
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key-change-this')

def connect_to_db():
    """Connect to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'numberplates_speed'),
            port=int(os.getenv('DB_PORT', '3306'))
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        return None

def hash_password(password):
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, hashed_password):
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

def generate_token(user_id, username, role):
    """Generate a JWT token for the user."""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token):
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}

def create_user(username, email, password, role='user'):
    """Create a new user in the database."""
    connection = connect_to_db()
    if not connection:
        return {'error': 'Database connection failed'}
    
    try:
        cursor = connection.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone():
            return {'error': 'User with this username or email already exists'}
        
        # Validate email
        if not validate_email(email):
            return {'error': 'Invalid email format'}
        
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            return {'error': message}
        
        # Hash password and insert user
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (username, email, hashed_password, role)
        )
        connection.commit()
        
        # Get the created user
        user_id = cursor.lastrowid
        
        return {
            'success': True, 
            'message': 'User created successfully',
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role
            }
        }
        
    except mysql.connector.Error as err:
        return {'error': f'Database error: {err}'}
    finally:
        cursor.close()
        connection.close()

def authenticate_user(username, password):
    """Authenticate a user and return a JWT token."""
    connection = connect_to_db()
    if not connection:
        return {'error': 'Database connection failed'}
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, username, email, password_hash, role, is_active FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            return {'error': 'Invalid credentials'}
        
        user_id, username, email, password_hash, role, is_active = user
        
        if not is_active:
            return {'error': 'Account is deactivated'}
        
        if not verify_password(password, password_hash):
            return {'error': 'Invalid credentials'}
        
        # Generate JWT token
        token = generate_token(user_id, username, role)
        
        return {
            'success': True,
            'token': token,
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role
            }
        }
        
    except mysql.connector.Error as err:
        return {'error': f'Database error: {err}'}
    finally:
        cursor.close()
        connection.close()

# Middleware for token verification
def token_required(f):
    """Decorator to require JWT token for protected routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = verify_token(token)
            if 'error' in payload:
                return jsonify(payload), 401
            
            request.current_user = payload
            
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

@app.route('/')
def home():
    return jsonify({
        "message": "Vehicle Detection API with Authentication", 
        "status": "running",
        "endpoints": {
            "POST /auth/signup": "User registration",
            "POST /auth/login": "User authentication",
            "GET /auth/verify": "Token verification",
            "GET /test": "Test endpoint"
        }
    })

@app.route('/auth/signup', methods=['POST'])
def signup():
    """User registration endpoint."""
    try:
        print("Signup attempt received")
        data = request.get_json()
        if not data:
            print("No data provided")
            return jsonify({'error': 'No data provided'}), 400
            
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'user')  # Default to 'user' role
        
        print(f"Signup attempt for username: {username}, email: {email}")
        
        if not all([username, email, password]):
            print("Missing required fields")
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        if role not in ['admin', 'user']:
            role = 'user'  # Default to user if invalid role provided
        
        result = create_user(username, email, password, role)
        print(f"User creation result: {result}")
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint."""
    try:
        print("Login attempt received")
        data = request.get_json()
        if not data:
            print("No data provided")
            return jsonify({'error': 'No data provided'}), 400
            
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        print(f"Login attempt for username: {username}")
        
        if not username or not password:
            print("Missing username or password")
            return jsonify({'error': 'Username and password are required'}), 400
        
        result = authenticate_user(username, password)
        print(f"Authentication result: {result}")
        
        if 'error' in result:
            return jsonify(result), 401
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/auth/verify', methods=['GET'])
@token_required
def verify_user_token():
    """Verify JWT token and return user info."""
    try:
        return jsonify({
            'valid': True,
            'user': {
                'id': request.current_user['user_id'],
                'username': request.current_user['username'],
                'role': request.current_user['role']
            }
        }), 200
    except Exception as e:
        return jsonify({'error': f'Token verification failed: {str(e)}'}), 500

@app.route('/auth/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current user profile."""
    try:
        return jsonify({
            'user': {
                'id': request.current_user['user_id'],
                'username': request.current_user['username'],
                'role': request.current_user['role']
            }
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint."""
    return jsonify({"message": "Test endpoint working", "status": "OK"})

@app.route('/users', methods=['GET'])
@token_required
def get_users():
    """Get all users (protected endpoint)."""
    try:
        connection = connect_to_db()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, email, role, created_at, is_active FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3],
                'created_at': user[4].isoformat() if user[4] else None,
                'is_active': user[5]
            })
        
        return jsonify({'users': user_list}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get users: {str(e)}'}), 500
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    print("Starting Flask authentication server...")
    print("Server will be available at: http://localhost:5001")
    print("Endpoints:")
    print("  POST /auth/signup - User registration")
    print("  POST /auth/login - User authentication") 
    print("  GET /auth/verify - Token verification")
    print("  GET /test - Test endpoint")
    app.run(debug=True, port=5001, host='localhost')