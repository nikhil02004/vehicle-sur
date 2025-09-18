import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import cv2
import numpy as np
import mysql.connector
from main import SpeedEstimator  # Import SpeedEstimator from main.py
from dotenv import load_dotenv
import bcrypt
import jwt
import re
from datetime import datetime, timedelta
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# JWT Configuration
# Security configuration from environment
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key-change-this')

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Load YOLO model
model_path = "models/best.pt"

def generate_output_video(input_video_path):
    """Processes video and saves the output with detections and speed estimations."""
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print("Error: Unable to open video file.")
        return None

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30  # Set default FPS if unavailable

    output_path = os.path.join(RESULT_FOLDER, "output.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_writer = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    # Initialize SpeedEstimator with proper database connection
    estimator = SpeedEstimator(region=[(0, 145), (1018, 145)], model=model_path, line_width=2)
    
    # Ensure the estimator is properly connected to database
    if estimator.db_connection is None:
        print("Warning: Database connection failed in SpeedEstimator")
    else:
        print("SpeedEstimator connected to database successfully")
    
    # Fetch and log current threshold
    current_threshold = estimator.get_threshold_speed()
    print(f"Processing video with speed threshold: {current_threshold} km/h")
    print(f"Email notifications enabled: {estimator.email_enabled}")

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        print(f"Processing frame {frame_count}")
        
        # Estimate speed and get detection results
        detection_results = estimator.estimate_speed(frame)
        
        # Get the annotated frame
        processed_frame = estimator.annotator.result()

        if processed_frame is not None and isinstance(processed_frame, np.ndarray):
            out_writer.write(processed_frame)
        
        # Log any violations found in this frame
        for result in detection_results:
            if result['status'] in ['BLACKLISTED', 'OVER SPEED']:
                print(f"VIOLATION DETECTED: {result['numberplate']} - {result['status']} at {result['speed']} km/h")

    cap.release()
    out_writer.release()
    
    # Close database connection
    if estimator.db_connection and estimator.db_connection.is_connected():
        estimator.db_connection.close()
        print("Database connection closed")
    
    print(f"Video processing completed. Output saved to: {output_path}")
    return output_path

def connect_to_db():
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'numberplates_speed'),
            port=int(os.getenv('DB_PORT', '3306'))
        )
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        return None

# Authentication Helper Functions
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
def index():
    return render_template('index.html')

@app.route('/results/<filename>')
def serve_result_video(filename):
    return send_from_directory(RESULT_FOLDER, filename)

@app.route('/upload', methods=["POST"])
def upload_video():
    try:
        # Validate file input
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
            
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Save uploaded file
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        print(f"File saved to: {file_path}")

        # Process video
        result_path = generate_output_video(file_path)
        if not result_path:
            return jsonify({"error": "Video processing failed"}), 500

        return jsonify({
            "message": "Video processed successfully",
            "result_video": result_path
        })

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Blacklist Management Routes
@app.route('/blacklist', methods=["POST"])
def manage_blacklist():
    data = request.get_json()
    action = data.get('action')
    numberplate = data.get('numberplate').replace(" ", "")

    if action == 'add':
        return add_to_blacklist(numberplate)
    elif action == 'remove':
        return remove_from_blacklist(numberplate)
    else:
        return jsonify({"error": "Invalid action"}), 400

def add_to_blacklist(numberplate):
    try:
        db_connection = connect_to_db()
        cursor = db_connection.cursor()
        query = "INSERT INTO blacklisted_vehicles (numberplate, reason) VALUES (%s, %s)"
        cursor.execute(query, (numberplate, "Added via API"))
        db_connection.commit()
        cursor.close()
        db_connection.close()
        return jsonify({"message": f"{numberplate} added to blacklist"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def remove_from_blacklist(numberplate):
    try:
        db_connection = connect_to_db()
        cursor = db_connection.cursor()
        query = "DELETE FROM blacklisted_vehicles WHERE numberplate = %s"
        cursor.execute(query, (numberplate,))
        db_connection.commit()
        cursor.close()
        db_connection.close()
        return jsonify({"message": f"{numberplate} removed from blacklist"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Speed Threshold Route
@app.route('/threshold', methods=['POST'])
def set_threshold():
    data = request.get_json()
    if not data or 'threshold' not in data:
        return jsonify({"error": "Invalid request format"}), 400
    
    threshold = data['threshold']
    
    try:
        conn = connect_to_db()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        # Create settings table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INT PRIMARY KEY AUTO_INCREMENT,
                threshold_speed FLOAT NOT NULL DEFAULT 50
            )
        """)
        
        # Initialize table with default value
        cursor.execute("INSERT INTO settings (threshold_speed) SELECT 50 WHERE NOT EXISTS (SELECT * FROM settings)")
        
        # Update threshold
        cursor.execute("UPDATE settings SET threshold_speed = %s WHERE id = 1", (float(threshold),))
        conn.commit()
        
        return jsonify({"message": f"Threshold updated to {threshold} km/h"})
        
    except ValueError:
        return jsonify({"error": "Invalid threshold value"}), 400
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if 'conn' in locals() and conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/threshold', methods=['GET'])
def get_threshold():
    """Get current speed threshold from database."""
    try:
        conn = connect_to_db()
        if not conn:
            return jsonify({"threshold": 50}), 200  # Return default on DB error
            
        cursor = conn.cursor()
        
        # Create settings table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INT PRIMARY KEY AUTO_INCREMENT,
                threshold_speed FLOAT NOT NULL DEFAULT 50
            )
        """)
        
        # Insert default record if none exists
        cursor.execute("INSERT INTO settings (threshold_speed) SELECT 50 WHERE NOT EXISTS (SELECT * FROM settings)")
        conn.commit()
        
        # Get current threshold
        cursor.execute("SELECT threshold_speed FROM settings WHERE id = 1")
        result = cursor.fetchone()
        
        if result:
            threshold = result[0]
        else:
            threshold = 50  # Default fallback
            
        return jsonify({"threshold": threshold})
        
    except Exception as e:
        print(f"Error getting threshold: {str(e)}")
        return jsonify({"threshold": 50}), 200  # Return default on error
    finally:
        if 'conn' in locals() and conn and conn.is_connected():
            cursor.close()
            conn.close()

# New Route for Analytics Dashboard
@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        conn = connect_to_db()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        # Total vehicles processed
        cursor.execute("SELECT COUNT(*) as total_vehicles FROM my_data")
        total_vehicles = cursor.fetchone()['total_vehicles']

        # Average speed
        cursor.execute("SELECT AVG(speed) as average_speed FROM my_data")
        avg_speed_result = cursor.fetchone()['average_speed']
        average_speed = round(avg_speed_result, 2) if avg_speed_result else 0.0

        # Number of overspeeding vehicles
        cursor.execute("SELECT COUNT(*) as overspeeding FROM my_data WHERE status = 'OVER SPEED'")
        overspeeding = cursor.fetchone()['overspeeding']

        # Number of blacklisted vehicles
        cursor.execute("SELECT COUNT(*) as blacklisted FROM my_data WHERE status = 'BLACKLISTED'")
        blacklisted = cursor.fetchone()['blacklisted']

        # Top 5 violators
        cursor.execute("""
            SELECT numberplate, COUNT(*) as violation_count 
            FROM my_data 
            WHERE status IN ('OVER SPEED', 'BLACKLISTED') 
            GROUP BY numberplate 
            ORDER BY violation_count DESC 
            LIMIT 5
        """)
        top_violators = cursor.fetchall()

        return jsonify({
            "total_vehicles": total_vehicles,
            "average_speed": average_speed,
            "overspeeding": overspeeding,
            "blacklisted": blacklisted,
            "top_violators": top_violators
        })

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if 'conn' in locals() and conn and conn.is_connected():
            cursor.close()
            conn.close()

# Email Configuration Route
@app.route('/email-config', methods=['POST'])
def set_email_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request format"}), 400
    
    sender_email = data.get('sender_email')
    sender_password = data.get('sender_password')
    receiver_email = data.get('receiver_email')
    
    if not all([sender_email, sender_password, receiver_email]):
        return jsonify({"error": "All email fields are required"}), 400
    
    try:
        conn = connect_to_db()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        # Create email_config table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_config (
                id INT PRIMARY KEY AUTO_INCREMENT,
                sender_email VARCHAR(255) NOT NULL,
                sender_password VARCHAR(255) NOT NULL,
                receiver_email VARCHAR(255) NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Delete existing config and insert new one
        cursor.execute("DELETE FROM email_config")
        cursor.execute("""
            INSERT INTO email_config (sender_email, sender_password, receiver_email) 
            VALUES (%s, %s, %s)
        """, (sender_email, sender_password, receiver_email))
        
        conn.commit()
        
        return jsonify({"message": "Email configuration updated successfully"})
        
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if 'conn' in locals() and conn and conn.is_connected():
            cursor.close()
            conn.close()

# Authentication Routes
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
    print("Starting unified backend server with authentication...")
    print("Server will be available at: http://localhost:5000")
    print("Available endpoints:")
    print("  - Authentication: /auth/login, /auth/signup, /auth/verify")
    print("  - Video processing: /upload")
    print("  - Blacklist management: /blacklist")
    print("  - Analytics: /stats")
    print("  - Test: /test")
    app.run(debug=True, port=5000, host='localhost')