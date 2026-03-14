import cv2
import threading
import time
from flask import Flask, render_template, Response, jsonify, request
from detector import PersonDetector
from tracker import PersonTracker
from counter import PeopleCounter

app = Flask(__name__)

# Global variables to store state
class AppState:
    def __init__(self):
        self.camera_active = False
        self.occupancy_limit = 50
        self.detection_sensitivity = 85
        self.current_count = 0
        self.total_entries = 0
        self.total_exits = 0
        self.fps = 0
        self.peak_today = 0
        self.history = [
            {"date": "Oct 24, 2023", "time": "09:00 AM - 06:00 PM", "total": 452, "peak": 85},
            {"date": "Oct 23, 2023", "time": "08:30 AM - 05:30 PM", "total": 318, "peak": 42},
            {"date": "Oct 22, 2023", "time": "10:00 AM - 04:00 PM", "total": 124, "peak": 18}
        ]

state = AppState()

# Initialize modules globally
print("Loading YOLOv8 model - initial load...")
detector = PersonDetector(model_path='yolov8n.pt')
print("YOLOv8 Loaded.")

tracker = PersonTracker(max_age=30, n_init=3)
counter = None

def generate_frames():
    global counter
    
    cap = cv2.VideoCapture(0) # or source
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    ret, frame = cap.read()
    if not ret:
        return
        
    height, width, _ = frame.shape
    line_y = int(height * 0.5)
    
    if counter is None:
        counter = PeopleCounter(line_y=line_y)
        
    prev_time = time.time()

    while state.camera_active:
        ret, frame = cap.read()
        if not ret:
            break

        # Calculate FPS
        current_time = time.time()
        fps_val = 1 / (current_time - prev_time) if current_time - prev_time > 0 else 0
        prev_time = current_time
        state.fps = fps_val

        # Detection & Tracking
        detections = detector.detect(frame)
        tracked_objects = tracker.update(frame, detections)
        current_visible_count = counter.update_and_count(tracked_objects)
        
        # Update State
        state.current_count = current_visible_count
        state.total_entries = counter.total_entries
        state.total_exits = counter.total_exits
        if current_visible_count > state.peak_today:
            state.peak_today = current_visible_count

        # Optional Drawing: Counter Line
        # cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 2)

        for track in tracked_objects:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            
            x1, y1, x2, y2 = map(int, track.to_ltrb())
            
            # Draw premium-looking Tracking BB
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 100, 0), 2)

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    if state.camera_active:
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return "Camera Inactive", 204

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify({
        "camera_active": state.camera_active,
        "current_count": state.current_count,
        "total_entries": state.total_entries,
        "total_exits": state.total_exits,
        "peak_today": state.peak_today,
        "limit": state.occupancy_limit,
        "fps": round(state.fps, 1),
        "history": state.history
    })

@app.route('/api/toggle_camera', methods=['POST'])
def toggle_camera():
    data = request.json
    state.camera_active = data.get('active', False)
    return jsonify({"status": "success", "camera_active": state.camera_active})

@app.route('/api/update_settings', methods=['POST'])
def update_settings():
    data = request.json
    if 'limit' in data:
        state.occupancy_limit = int(data['limit'])
    if 'sensitivity' in data:
        state.detection_sensitivity = int(data['sensitivity'])
    return jsonify({"status": "success"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
