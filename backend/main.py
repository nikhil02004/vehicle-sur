import cv2
from time import time
import numpy as np
from ultralytics.solutions.solutions import BaseSolution
from ultralytics.utils.plotting import Annotator, colors
from datetime import datetime
import mysql.connector
from paddleocr import PaddleOCR
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import email configuration
try:
    from email_config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER, SMTP_SERVER, SMTP_PORT, EMAIL_ENABLED
except ImportError:
    # Fallback to environment variables if config file doesn't exist
    EMAIL_SENDER = os.getenv('EMAIL_SENDER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'true').lower() == 'true'

class SpeedEstimator(BaseSolution):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initialize_region()
        self.spd = {}  # Stores calculated speed values
        self.trkd_ids = []
        self.trk_pt = {}  # Stores previous timestamps
        self.trk_pp = {}  # Stores previous positions
        self.logged_ids = set()
        # Initialize PaddleOCR
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
        self.db_connection = self.connect_to_db()
        self.speed_threshold = 50  # Default speed threshold
        # Email configuration
        self.email_sender = EMAIL_SENDER
        self.email_password = EMAIL_PASSWORD
        self.email_receiver = EMAIL_RECEIVER
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.email_enabled = EMAIL_ENABLED

    def connect_to_db(self):
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="nikhil",
                database="numberplates_speed"
            )
            return connection
        except mysql.connector.Error as err:
            print(f"Error connecting to database: {err}")
            return None

    def perform_ocr(self, image_array):
        if isinstance(image_array, np.ndarray):
            results = self.ocr.ocr(image_array, rec=True)
            if results and results[0]:
                return ' '.join([result[1][0] for result in results[0]])
        return ""

    def save_to_database(self, date, time, track_id, class_name, speed, numberplate, status=""):
        if not self.db_connection:
            print("Database connection not available. Skipping save.")
            return
        try:
            cursor = self.db_connection.cursor()
            query = """
                INSERT INTO my_data (date, time, track_id, class_name, speed, numberplate, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (date, time, track_id, class_name, speed, numberplate.replace(" ", ""), status))
            self.db_connection.commit()
        except mysql.connector.Error as err:
            print(f"Error saving to database: {err}")

    def is_blacklisted(self, numberplate):
        if not self.db_connection or not numberplate:
            return False
        try:
            cursor = self.db_connection.cursor()
            query = "SELECT EXISTS(SELECT 1 FROM blacklisted_vehicles WHERE numberplate = %s)"
            cursor.execute(query, (numberplate,))
            result = cursor.fetchone()
            return result[0] == 1
        except Exception as e:
            print(f"Blacklist check error for {numberplate}: {str(e)}")
            return False

    def send_email(self, numberplate, speed, status):
        """Send email notification for blacklisted or overspeeding vehicles."""
        if not self.email_enabled:
            print("Email notifications are disabled")
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_sender
            msg['To'] = self.email_receiver
            msg['Subject'] = f"Vehicle Violation Alert: {status}"

            body = f"""
            A vehicle violation has been detected:
            Number Plate: {numberplate}
            Speed: {speed} km/h
            Status: {status}
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.sendmail(self.email_sender, self.email_receiver, msg.as_string())
            print(f"Email sent for {status} vehicle: {numberplate}")
        except Exception as e:
            print(f"Failed to send email: {str(e)}")

    def get_threshold_speed(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT threshold_speed FROM settings WHERE id = 1")
            result = cursor.fetchone()
            return result[0] if result else 50.0
        except Exception as e:
            print(f"Threshold fetch error: {str(e)}")
            return 50.0

    def estimate_speed(self, im0):
        self.annotator = Annotator(im0, line_width=self.line_width)
        self.extract_tracks(im0)
        current_time = datetime.now()
        results = []

        # Fetch threshold speed from database
        threshold_speed = self.get_threshold_speed()
        print(f"Current threshold: {threshold_speed} km/h")

        for box, track_id, cls in zip(self.boxes, self.track_ids, self.clss):
            x1, y1, x2, y2 = map(int, box)
            cropped_image = np.array(im0)[y1:y2, x1:x2]
            ocr_text = self.perform_ocr(cropped_image).strip().replace(" ", "")  # Normalize OCR text
            class_name = self.names[int(cls)]

            if track_id not in self.trk_pt:
                self.trk_pt[track_id] = time()
                self.trk_pp[track_id] = box

            current_time_sec = time()
            time_diff = current_time_sec - self.trk_pt[track_id]

            if track_id not in self.spd and time_diff > 0.05:  
                prev_center = np.array([(self.trk_pp[track_id][0] + self.trk_pp[track_id][2]) / 2,
                                        (self.trk_pp[track_id][1] + self.trk_pp[track_id][3]) / 2])
                curr_center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])

                distance_moved = np.linalg.norm(curr_center - prev_center)
                avg_speed_kmh = (distance_moved / time_diff) * 3.6
                self.spd[track_id] = round(avg_speed_kmh, 2)

            speed = self.spd.get(track_id, 0)
            self.trk_pt[track_id] = current_time_sec
            self.trk_pp[track_id] = box

            # Debugging prints
            print(f"Track ID {track_id} | Speed: {speed} km/h | Plate: {ocr_text}")

            # Initialize values
            color = (0, 128, 0)  # DARK GREEN (BGR format)
            status = ""
            text = f"{ocr_text} | {speed} km/h"

            # Blacklist check with normalization
            if ocr_text and self.is_blacklisted(ocr_text):
                print(f"BLACKLIST DETECTED: {ocr_text}")
                color = (0, 0, 255)  # RED
                status = "BLACKLISTED"
                text = f"{ocr_text} | BLACKLISTED | {speed} km/h"
            elif speed > threshold_speed:
                color = (255, 0, 0)  # BLUE
                status = "OVER SPEED"
                text = f"{ocr_text} | OVER SPEED | {speed} km/h"

            # Always draw the box
            self.annotator.box_label((x1, y1, x2, y2), text, color=color)

            # Database logging and email notification - only log if speed has been calculated
            if track_id not in self.logged_ids and ocr_text and track_id in self.spd:
                self.save_to_database(
                    current_time.strftime("%Y-%m-%d"),
                    current_time.strftime("%H:%M:%S"),
                    track_id,
                    class_name,
                    speed,
                    ocr_text,
                    status
                )
                # Send email if the vehicle is blacklisted or overspeeding
                if status in ["BLACKLISTED", "OVER SPEED"]:
                    self.send_email(ocr_text, speed, status)
                self.logged_ids.add(track_id)

            results.append({
                "track_id": track_id,
                "class_name": class_name,
                "speed": speed,
                "numberplate": ocr_text,
                "status": status
            })

        return results