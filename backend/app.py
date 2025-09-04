from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import cv2
import numpy as np
import mysql.connector
from main import SpeedEstimator  # Import SpeedEstimator from main.py

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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

    estimator = SpeedEstimator(region=[(0, 145), (1018, 145)], model=model_path, line_width=2)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        detection_results = estimator.estimate_speed(frame)
        processed_frame = estimator.annotator.result()

        if processed_frame is not None and isinstance(processed_frame, np.ndarray):
            out_writer.write(processed_frame)

    cap.release()
    out_writer.release()
    return output_path

def connect_to_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="nikhil",  # Updated to correct password
            database="numberplates_speed",
            port=3306  # Explicitly specify default MySQL port
        )
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        return None

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
        estimator = SpeedEstimator()  # Initialize if needed
        db_connection = estimator.connect_to_db()
        cursor = db_connection.cursor()
        query = "INSERT INTO blacklisted_vehicles (numberplate, reason) VALUES (%s, %s)"
        cursor.execute(query, (numberplate, "Added via API"))
        db_connection.commit()
        return jsonify({"message": f"{numberplate} added to blacklist"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def remove_from_blacklist(numberplate):
    try:
        estimator = SpeedEstimator()  # Initialize if needed
        db_connection = estimator.connect_to_db()
        cursor = db_connection.cursor()
        query = "DELETE FROM blacklisted_vehicles WHERE numberplate = %s"
        cursor.execute(query, (numberplate,))
        db_connection.commit()
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

if __name__ == "__main__":
    app.run(debug=True)