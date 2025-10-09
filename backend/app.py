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
    all_detection_results = []  # Collect all detection results for pollution processing
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        print(f"Processing frame {frame_count}")
        
        # Estimate speed and get detection results
        detection_results = estimator.estimate_speed(frame)
        
        # Collect detection results for pollution processing
        if detection_results:
            all_detection_results.extend(detection_results)
        
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
    
    # Process pollution data after video processing
    video_filename = os.path.basename(input_video_path)
    print(f"\nProcessing pollution data for video: {video_filename}")
    print(f"Total detection results collected: {len(all_detection_results)}")
    
    if all_detection_results:
        process_video_pollution_data(all_detection_results, video_filename)
    else:
        print("No detection results found for pollution processing")
    
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

# Pollution Calculation Functions
def get_vehicle_emission_rate(numberplate):
    """Get emission rate for a vehicle from database, create mock data if not found."""
    conn = connect_to_db()
    if not conn:
        return 150.0  # Default emission rate
    
    cursor = conn.cursor()
    try:
        # Check if vehicle exists
        cursor.execute("SELECT emission_rate FROM vehicle_pollution WHERE numberplate = %s", (numberplate,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            # Create mock data for missing vehicle
            mock_emission_rate = create_mock_vehicle_data(numberplate)
            return mock_emission_rate
            
    except mysql.connector.Error as err:
        print(f"Database error getting emission rate: {err}")
        return 150.0  # Default fallback
    finally:
        cursor.close()
        conn.close()

def create_mock_vehicle_data(numberplate):
    """Create mock emission data for a vehicle not in database."""
    conn = connect_to_db()
    if not conn:
        return 150.0
    
    cursor = conn.cursor()
    try:
        # Determine fuel type based on numberplate patterns
        fuel_type = 'petrol'  # Default
        emission_rate = 150.0  # Default
        
        plate_upper = numberplate.upper()
        if 'E' in plate_upper or 'EV' in plate_upper:
            fuel_type = 'electric'
            emission_rate = 0.0
        elif 'D' in plate_upper or 'DL' in plate_upper:
            fuel_type = 'diesel'
            emission_rate = 180.0 + (hash(numberplate) % 40)  # 180-220 range
        elif 'C' in plate_upper or 'CNG' in plate_upper:
            fuel_type = 'CNG'
            emission_rate = 120.0 + (hash(numberplate) % 30)  # 120-150 range
        elif 'H' in plate_upper or 'HY' in plate_upper:
            fuel_type = 'hybrid'
            emission_rate = 90.0 + (hash(numberplate) % 30)   # 90-120 range
        else:
            # Petrol vehicles - vary based on numberplate hash
            emission_rate = 150.0 + (hash(numberplate) % 50)  # 150-200 range
        
        # Insert mock data
        cursor.execute("""
            INSERT IGNORE INTO vehicle_pollution (numberplate, fuel_type, emission_rate)
            VALUES (%s, %s, %s)
        """, (numberplate, fuel_type, emission_rate))
        
        conn.commit()
        print(f"Created mock data for {numberplate}: {fuel_type}, {emission_rate} g/km")
        return emission_rate
        
    except mysql.connector.Error as err:
        print(f"Database error creating mock data: {err}")
        return 150.0
    finally:
        cursor.close()
        conn.close()

def calculate_speed_adjusted_emission(base_emission_rate, speed):
    """Calculate emission based on speed. Higher speeds = higher emissions."""
    if speed <= 0:
        return 0.0
    
    # Base calculation: emission per km at given speed
    # Speed factor increases exponentially for higher speeds
    if speed <= 30:
        speed_factor = 0.8  # Lower emissions at low speeds
    elif speed <= 60:
        speed_factor = 1.0  # Normal emissions
    elif speed <= 80:
        speed_factor = 1.3  # 30% increase
    elif speed <= 100:
        speed_factor = 1.6  # 60% increase
    else:
        speed_factor = 2.0  # Double emissions for very high speeds
    
    # Calculate emission for a small distance (assuming detection over short segment)
    # Assume each detection represents ~0.1 km of travel
    segment_distance = 0.1  # km
    
    total_emission = base_emission_rate * speed_factor * segment_distance
    return round(total_emission, 2)

def extract_location_from_filename(filename):
    """Extract location name from video filename."""
    if not filename:
        return "unknown"
    
    # Remove file extension and convert to lowercase
    location = os.path.splitext(filename)[0].lower()
    
    # Map known locations
    location_mapping = {
        'kiit': 'kiit',
        'shikharchandi': 'shikharchandi', 
        'udaygiri': 'udaygiri'
    }
    
    # Check if filename contains any known location
    for key, value in location_mapping.items():
        if key in location:
            return value
    
    return location  # Return as-is if no mapping found

def update_location_emission(location, date, total_pollution, vehicles_count, avg_speed, replace=False):
    """Update or insert location emission data."""
    conn = connect_to_db()
    if not conn:
        print("Failed to connect to database for location emission update")
        return False
    
    cursor = conn.cursor()
    try:
        if replace:
            # Replace existing record completely (for single video uploads)
            cursor.execute("""
                INSERT INTO location_emission (location, date, total_pollution, vehicles_passed, avg_speed)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                total_pollution = VALUES(total_pollution),
                vehicles_passed = VALUES(vehicles_passed),
                avg_speed = VALUES(avg_speed)
            """, (location, date, total_pollution, vehicles_count, avg_speed))
            
            print(f"Replaced location emission for {location} on {date}: {total_pollution:.2f}g, {vehicles_count} vehicles, {avg_speed:.1f} km/h avg")
        else:
            # Check if record exists for this location and date
            cursor.execute("""
                SELECT total_pollution, vehicles_passed, avg_speed 
                FROM location_emission 
                WHERE location = %s AND date = %s
            """, (location, date))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record - add to existing values
                new_total_pollution = existing[0] + total_pollution
                new_vehicles_count = existing[1] + vehicles_count
                new_avg_speed = ((existing[2] * existing[1]) + (avg_speed * vehicles_count)) / new_vehicles_count
                
                cursor.execute("""
                    UPDATE location_emission 
                    SET total_pollution = %s, vehicles_passed = %s, avg_speed = %s
                    WHERE location = %s AND date = %s
                """, (new_total_pollution, new_vehicles_count, new_avg_speed, location, date))
                
                print(f"Updated location emission for {location} on {date}: {new_total_pollution:.2f}g, {new_vehicles_count} vehicles")
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO location_emission (location, date, total_pollution, vehicles_passed, avg_speed)
                    VALUES (%s, %s, %s, %s, %s)
                """, (location, date, total_pollution, vehicles_count, avg_speed))
                
                print(f"Inserted new location emission for {location} on {date}: {total_pollution:.2f}g, {vehicles_count} vehicles")
        
        conn.commit()
        return True
        
    except mysql.connector.Error as err:
        print(f"Database error updating location emission: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def process_video_pollution_data(detection_results, video_filename):
    """Process detection results and update location emission data using temp_vehicle table for accurate counting."""
    if not detection_results:
        print("No detection results to process for pollution data")
        return
    
    location = extract_location_from_filename(video_filename)
    current_date = datetime.now().date()
    
    # Connect to database for temp_vehicle operations
    conn = connect_to_db()
    if not conn:
        print("Failed to connect to database for pollution processing")
        return
    
    cursor = conn.cursor()
    
    try:
        print(f"Processing pollution data for location: {location}")
        print(f"Total detection events: {len(detection_results)}")
        
        # Step 1: Clear temp_vehicle table for this video session
        cursor.execute("DELETE FROM temp_vehicle")
        conn.commit()
        print("Cleared temp_vehicle table for new video session")
        
        # Step 2: Use set to get ONLY unique numberplates - no duplicates allowed
        print(f"Sample detection results (first 5):")
        for i, result in enumerate(detection_results[:5]):
            print(f"  {i+1}: numberplate='{result.get('numberplate')}', speed={result.get('speed')}")
        
        # Use set to collect unique numberplates only
        unique_numberplates = set()
        unique_vehicle_data = {}  # Store only ONE representative speed per unique vehicle
        
        for result in detection_results:
            numberplate = result.get('numberplate')
            speed = result.get('speed', 0)
            
            if not numberplate or speed <= 0:
                continue
            
            # Only add to set if not already present
            if numberplate not in unique_numberplates:
                unique_numberplates.add(numberplate)
                unique_vehicle_data[numberplate] = speed  # Store ONLY the first valid speed
                print(f"Found unique vehicle: {numberplate} with speed {speed} km/h")
            # If vehicle already seen, ignore this detection completely
        
        print(f"Total detections processed: {len(detection_results)}")
        print(f"Unique numberplates found (using set): {len(unique_numberplates)}")
        print(f"Unique numberplates: {sorted(list(unique_numberplates))}")
        
        # Step 3: Insert unique vehicles into temp_vehicle table 
        vehicle_detections = {}  # Store data for pollution calculation
        
        for numberplate in unique_numberplates:
            try:
                cursor.execute("""
                    INSERT INTO temp_vehicle (numberplate, video_filename) 
                    VALUES (%s, %s)
                """, (numberplate, video_filename))
                
                # Store ONE speed value for this unique vehicle (for pollution calculation)
                vehicle_detections[numberplate] = [unique_vehicle_data[numberplate]]  # Single speed in list
                print(f"Added unique vehicle: {numberplate} with speed {unique_vehicle_data[numberplate]} km/h")
                
            except mysql.connector.IntegrityError:
                print(f"Vehicle {numberplate} already exists in temp_vehicle (unexpected)")
            except mysql.connector.Error as e:
                print(f"Error inserting vehicle {numberplate}: {e}")
                continue
        
        conn.commit()
        
        # Step 4: Verify counts match
        cursor.execute("SELECT COUNT(*) FROM temp_vehicle WHERE video_filename = %s", (video_filename,))
        temp_vehicle_count = cursor.fetchone()[0]
        
        print(f"=== UNIQUE VEHICLE COUNT VERIFICATION ===")
        print(f"Unique vehicles from set: {len(unique_numberplates)}")
        print(f"Vehicles in temp_vehicle table: {temp_vehicle_count}")
        print(f"Vehicles to process for pollution: {len(vehicle_detections)}")
        print(f"Vehicle details:")
        for plate, speeds in vehicle_detections.items():
            print(f"  {plate}: {len(speeds)} detections, max speed: {max(speeds)} km/h")
        
        # Step 5: Calculate pollution for unique vehicles only
        total_pollution = 0.0
        vehicle_count = len(unique_numberplates)  # Use set size for absolute accuracy
        total_speed = 0.0
        
        print(f"Final calculation using {vehicle_count} unique vehicles:")
        
        for numberplate, speeds in vehicle_detections.items():
            # Use the maximum speed detected for this vehicle (most accurate for emission calculation)
            max_speed = max(speeds)
            avg_speed_for_vehicle = sum(speeds) / len(speeds)
            
            # Get emission rate for this vehicle
            emission_rate = get_vehicle_emission_rate(numberplate)
            
            # Calculate emission using the maximum speed (worst case scenario)
            vehicle_emission = calculate_speed_adjusted_emission(emission_rate, max_speed)
            
            total_pollution += vehicle_emission
            total_speed += avg_speed_for_vehicle  # Use average speed for overall calculation
            
            print(f"Vehicle {numberplate}: detected {len(speeds)} times, max speed {max_speed} km/h, avg speed {avg_speed_for_vehicle:.1f} km/h, {emission_rate} g/km base, {vehicle_emission}g emission")
        
        if vehicle_count > 0:
            overall_avg_speed = total_speed / vehicle_count
            
            # Update location emission data - use replace=True for single video uploads
            success = update_location_emission(location, current_date, total_pollution, vehicle_count, overall_avg_speed, replace=True)
            
            if success:
                print(f"Successfully updated pollution data for {location}: {total_pollution:.2f}g total, {vehicle_count} unique vehicles, {overall_avg_speed:.1f} km/h avg")
            else:
                print(f"Failed to update pollution data for {location}")
        else:
            print("No valid vehicles detected for pollution calculation")
    
    except mysql.connector.Error as err:
        print(f"Database error during pollution processing: {err}")
    except Exception as e:
        print(f"Unexpected error during pollution processing: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

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
@app.route('/blacklist', methods=["GET"])
@token_required
def get_blacklist():
    """Get all blacklisted vehicles."""
    try:
        db_connection = connect_to_db()
        if not db_connection:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute("SELECT id, numberplate, reason FROM blacklisted_vehicles ORDER BY id DESC")
        blacklisted_vehicles = cursor.fetchall()
        cursor.close()
        db_connection.close()
        
        # Transform to match frontend expected format
        result = []
        for vehicle in blacklisted_vehicles:
            result.append({
                "license_plate": vehicle["numberplate"],
                "reason": vehicle["reason"]
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/blacklist', methods=["POST"])
@token_required
def manage_blacklist():
    data = request.get_json()
    action = data.get('action')
    numberplate = data.get('numberplate').replace(" ", "")
    reason = data.get('reason', 'Added via API')

    if action == 'add':
        return add_to_blacklist(numberplate, reason)
    elif action == 'remove':
        return remove_from_blacklist(numberplate)
    else:
        return jsonify({"error": "Invalid action"}), 400

def add_to_blacklist(numberplate, reason="Added via API"):
    try:
        db_connection = connect_to_db()
        cursor = db_connection.cursor()
        query = "INSERT INTO blacklisted_vehicles (numberplate, reason) VALUES (%s, %s)"
        cursor.execute(query, (numberplate, reason))
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

# Pollution Data API Endpoints
@app.route('/pollution/locations', methods=['GET'])
@token_required
def get_pollution_by_locations():
    """Get pollution data grouped by locations."""
    try:
        conn = connect_to_db()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Get pollution summary by location for recent dates
        cursor.execute("""
            SELECT 
                location,
                DATE(date) as date,
                total_pollution,
                vehicles_passed,
                avg_speed,
                CASE 
                    WHEN total_pollution < 100 THEN 'Low'
                    WHEN total_pollution < 500 THEN 'Medium'
                    ELSE 'High'
                END as pollution_level
            FROM location_emission 
            ORDER BY date DESC, total_pollution DESC
            LIMIT 100
        """)
        
        results = cursor.fetchall()
        
        # Convert date objects to strings for JSON serialization
        for result in results:
            if result['date']:
                result['date'] = result['date'].strftime('%Y-%m-%d')
        
        return jsonify(results)
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if 'conn' in locals() and conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/pollution/summary', methods=['GET'])
@token_required
def get_pollution_summary():
    """Get overall pollution summary statistics."""
    try:
        conn = connect_to_db()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Get overall statistics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT location) as total_locations,
                COALESCE(SUM(total_pollution), 0) as total_emissions,
                COALESCE(SUM(vehicles_passed), 0) as total_vehicles,
                COALESCE(AVG(avg_speed), 0) as overall_avg_speed,
                MAX(date) as latest_data_date
            FROM location_emission
        """)
        
        summary = cursor.fetchone()
        
        # Handle empty summary case
        if not summary or summary['total_locations'] == 0:
            summary = {
                'total_locations': 0,
                'total_emissions': 0,
                'total_vehicles': 0,
                'overall_avg_speed': 0,
                'latest_data_date': None
            }
        
        # Get top polluting locations
        cursor.execute("""
            SELECT 
                location,
                COALESCE(SUM(total_pollution), 0) as total_pollution,
                COALESCE(SUM(vehicles_passed), 0) as total_vehicles,
                COALESCE(AVG(avg_speed), 0) as avg_speed
            FROM location_emission 
            GROUP BY location
            ORDER BY total_pollution DESC
            LIMIT 5
        """)
        
        top_locations = cursor.fetchall()
        
        # Ensure top_locations is not None
        if not top_locations:
            top_locations = []
        
        # Get recent daily trends
        cursor.execute("""
            SELECT 
                DATE(date) as date,
                COALESCE(SUM(total_pollution), 0) as daily_pollution,
                COALESCE(SUM(vehicles_passed), 0) as daily_vehicles
            FROM location_emission 
            WHERE date >= DATE(NOW() - INTERVAL 7 DAY)
            GROUP BY DATE(date)
            ORDER BY date DESC
        """)
        
        daily_trends = cursor.fetchall()
        
        # Ensure daily_trends is not None
        if not daily_trends:
            daily_trends = []
        
        # Convert date objects to strings
        if summary and summary['latest_data_date']:
            summary['latest_data_date'] = summary['latest_data_date'].strftime('%Y-%m-%d')
        
        for trend in daily_trends:
            if trend['date']:
                trend['date'] = trend['date'].strftime('%Y-%m-%d')
        
        return jsonify({
            "summary": summary,
            "top_locations": top_locations,
            "daily_trends": daily_trends
        })
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if 'conn' in locals() and conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/pollution/location/<location>', methods=['GET'])
@token_required
def get_pollution_by_location(location):
    """Get detailed pollution data for a specific location."""
    try:
        conn = connect_to_db()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Get pollution data for specific location
        cursor.execute("""
            SELECT 
                DATE(date) as date,
                total_pollution,
                vehicles_passed,
                avg_speed,
                CASE 
                    WHEN total_pollution < 100 THEN 'Low'
                    WHEN total_pollution < 500 THEN 'Medium'
                    ELSE 'High'
                END as pollution_level
            FROM location_emission 
            WHERE location = %s
            ORDER BY date DESC
            LIMIT 30
        """, (location,))
        
        results = cursor.fetchall()
        
        # Convert date objects to strings
        for result in results:
            if result['date']:
                result['date'] = result['date'].strftime('%Y-%m-%d')
        
        # Get vehicles that contributed to pollution at this location
        cursor.execute("""
            SELECT DISTINCT md.numberplate, vp.fuel_type, vp.emission_rate
            FROM my_data md
            LEFT JOIN vehicle_pollution vp ON md.numberplate = vp.numberplate
            WHERE md.location = %s OR LOWER(md.video_source) LIKE %s
            LIMIT 20
        """, (location, f'%{location}%'))
        
        vehicles = cursor.fetchall()
        
        return jsonify({
            "location": location,
            "pollution_data": results,
            "contributing_vehicles": vehicles
        })
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
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

@app.route('/user-dashboard', methods=['GET'])
@token_required
def get_user_dashboard():
    """Get dashboard data for a specific user (numberplate)."""
    try:
        # Get the username from the authenticated user (which will be the numberplate)
        username = request.current_user['username']
        
        connection = connect_to_db()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get all records for this numberplate
        cursor.execute("SELECT * FROM my_data WHERE numberplate = %s", (username,))
        records = cursor.fetchall()
        
        # Calculate metrics
        total_passes = len(records)
        violations = len([r for r in records if r['status'] in ['OVER SPEED', 'BLACKLISTED']])
        
        # Check if blacklisted
        cursor.execute("SELECT COUNT(*) as count FROM blacklisted_vehicles WHERE numberplate = %s", (username,))
        is_blacklisted = cursor.fetchone()['count'] > 0
        
        # Calculate average speed
        speeds = [r['speed'] for r in records if r['speed'] is not None]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'data': {
                'numberplate': username,
                'times_passed': total_passes,
                'violations': violations,
                'is_blacklisted': is_blacklisted,
                'avg_speed': round(avg_speed, 2)
            }
        }), 200
        
    except Exception as e:
        print(f"User dashboard error: {e}")
        return jsonify({'error': f'Failed to get dashboard data: {str(e)}'}), 500

if __name__ == "__main__":
    print("Starting unified backend server with authentication...")
    print("Server will be available at: http://localhost:5000")
    print("Available endpoints:")
    print("  - Authentication: /auth/login, /auth/signup, /auth/verify")
    print("  - Video processing: /upload")
    print("  - Blacklist management: /blacklist")
    print("  - Analytics: /stats")
    print("  - Pollution data: /pollution/locations, /pollution/summary, /pollution/location/<location>")
    print("  - User Dashboard: /user-dashboard")
    print("  - Test: /test")
    app.run(debug=True, port=5000, host='localhost')