# Vehicle Detection Dashboard

A React frontend with TailwindCSS that connects to a Flask backend for vehicle detection, speed estimation, and number plate recognition.

# Vehicle Detection Dashboard

A React frontend with TailwindCSS that connects to a Flask backend for vehicle detection, speed estimation, and number plate recognition.

## Project Structure

```
react-front-vehicle-detection-api/
├── backend/                    # Flask backend
│   ├── .venv/                 # Python virtual environment
│   ├── app.py                 # Main Flask application
│   ├── main.py                # Speed estimation logic
│   ├── config.py              # Configuration
│   ├── models/                # YOLO model files
│   ├── uploads/               # Uploaded videos
│   ├── results/               # Processed videos
│   ├── templates/             # Flask templates (legacy)
│   ├── requirements.txt       # Python dependencies
│   └── start_app.bat          # Backend start script
├── frontend/                  # React frontend
│   ├── src/                   # React source code
│   ├── public/                # Static assets
│   ├── package.json           # Node.js dependencies
│   └── ...                    # Other React files
├── start_full_app.bat         # Start both servers
└── README.md                  # This file
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Activate the virtual environment:
   ```bash
   .venv\Scripts\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements_fixed.txt
   pip install flask-cors
   ```
4. Make sure MySQL is running and the database is configured
5. Start the Flask backend:
   ```bash
   python app.py
   ```

The backend will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. Start the React development server:
   ```bash
   npm start
   ```

The frontend will run on `http://localhost:3000`

### Quick Start

Use the provided batch file to start both servers:
```bash
start_full_app.bat
```

This will automatically start both the Flask backend and React frontend in separate terminal windows.

## Features

### 🎥 Video Upload & Processing
- Drag & drop video upload interface
- Real-time video processing with YOLO object detection
- Speed estimation and number plate recognition
- View processed videos with annotations

### 📊 Analytics Dashboard
- Total vehicles processed
- Average speed statistics
- Overspeeding violations count
- Blacklisted vehicles count
- Top violators list

### 🚫 Blacklist Management
- Add vehicles to blacklist
- Remove vehicles from blacklist
- Automatic number plate formatting

### ⚙️ Settings
- Configure speed threshold
- Quick preset speed limits
- Real-time threshold updates

## API Endpoints

- `POST /upload` - Upload and process video
- `GET /stats` - Get analytics data
- `POST /blacklist` - Manage blacklist (add/remove)
- `POST /threshold` - Set speed threshold
- `GET /results/<filename>` - Serve processed videos

## Technology Stack

### Frontend
- **React 19** with TypeScript
- **TailwindCSS** for styling
- **React Router** for navigation
- **Axios** for HTTP requests
- **Lucide React** for icons

### Backend
- **Flask** with Python
- **YOLO** for object detection
- **OpenCV** for video processing
- **MySQL** for data storage
- **Flask-CORS** for cross-origin requests

## Usage

1. Start both backend and frontend servers
2. Open `http://localhost:3000` in your browser
3. Upload a video file for processing
4. View analytics, manage blacklist, and configure settings
5. Monitor processed videos and statistics

## Notes

- Make sure MySQL database is running and properly configured
- The backend serves processed videos from the `results/` directory
- All number plates are automatically converted to uppercase
- Speed calculations are based on AI detection and frame analysis
