# Vehicle Detection Backend

Flask-based backend for vehicle detection, speed estimation, and number plate recognition using YOLO models.

## Features

- Video upload and processing
- Real-time vehicle detection using YOLO
- Speed estimation based on vehicle movement
- Number plate recognition and blacklist management
- MySQL database integration
- REST API endpoints for frontend integration

## API Endpoints

- `POST /upload` - Upload and process video files
- `GET /stats` - Get analytics and statistics
- `POST /blacklist` - Manage vehicle blacklist (add/remove)
- `POST /threshold` - Set speed threshold
- `GET /results/<filename>` - Serve processed video files

## Setup

1. Activate virtual environment: `.venv\Scripts\activate`
2. Install dependencies: `pip install -r requirements_fixed.txt`
3. Configure MySQL database settings in the code
4. Run: `python app.py`

## Dependencies

- Flask - Web framework
- OpenCV - Computer vision
- YOLO - Object detection
- MySQL Connector - Database integration
- Flask-CORS - Cross-origin resource sharing
