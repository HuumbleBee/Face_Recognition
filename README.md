# Face Recognition Attendance System

## Overview
This project is a **Face Recognition-based Attendance System** that uses OpenCV and `face_recognition` library to detect and recognize faces. It allows users to register their faces, mark attendance, and manage attendance data via an API.

## Features
- **Face Registration**: Users can register their faces using a webcam.
- **Face Recognition**: The system recognizes faces and marks attendance.
- **Attendance Tracking**: Attendance is recorded locally in a CSV file and sent to an API.
- **Database Management**: Supports adding and deleting users.
- **Automated Attendance Time Slots**: Users can only mark attendance within predefined time slots.
- **Multi-threading for Performance**: Uses concurrent execution for better efficiency.

## Technologies Used
- **Python 3.x**
- **OpenCV** (`cv2`)
- **face_recognition**
- **NumPy**
- **Tkinter** (GUI)
- **Requests** (API communication)
- **CSV & JSON** (Data storage)
- **Pickle** (Face encoding storage)

## System Requirements
- Python 3.x
- A webcam
- Internet connection (for API communication)
- Required Python libraries (install with `pip install -r requirements.txt`)

## Installation
1. Clone this repository:
   ```sh
   git clone https://github.com/your-username/face-recognition-attendance.git
   cd face-recognition-attendance
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the application:
   ```sh
   python main.py
   ```

## Usage
### 1. Register a User
- Enter **ID** and **Name** in the GUI.
- The system captures multiple face images and stores encodings.
- Data is saved locally and sent to an API.

### 2. Mark Attendance
- The system recognizes faces in real time.
- Attendance is recorded **only within allowed time slots**.
- Data is stored in `attendance.csv` and sent to an API.

### 3. Delete a User
- Enter **ID** and **Name**, then click **Delete**.
- Data is removed from both local storage and the API.

## Attendance Time Slots
| Session | Start Time | End Time |
|---------|------------|----------|
| Morning | 05:00 AM  | 12:00 PM |
| Evening | 03:00 PM  | 11:00 PM |

## File Structure
```
face-recognition-attendance/
├── dataset/             # Stores registered face images
├── encodings.pickle     # Stores face encodings
├── attendance.csv       # Stores attendance records
├── main.py              # Main application script
├── requirements.txt     # Required dependencies
└── README.md            # Project documentation
```

## API Endpoints
- **Employee Registration**: `POST https://visagium-api.onrender.com/Employee`
- **Delete Employee**: `DELETE https://visagium-api.onrender.com/Employee`
- **Submit Attendance**: `POST https://visagium-api.onrender.com/Attendance`

## Troubleshooting
- **Face Not Detected**: Ensure proper lighting and adjust camera angle.
- **API Not Responding**: Check internet connection and API status.
- **Performance Issues**: Close unnecessary apps and ensure your PC meets hardware requirements.

## Contributing
Feel free to contribute by submitting issues or pull requests.

## License
MIT License

