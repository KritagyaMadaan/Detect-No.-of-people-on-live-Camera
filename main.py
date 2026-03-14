import cv2
import argparse
import time
from detector import PersonDetector
from tracker import PersonTracker
from counter import PeopleCounter

def main():
    parser = argparse.ArgumentParser(description="Real-Time People Counting system with YOLOv8 & DeepSORT")
    parser.add_argument("--source", type=str, default="0", help="Camera source (0 for webcam) or video file path")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Path to YOLOv8 model")
    args = parser.parse_args()

    # Determine generic source
    source = int(args.source) if args.source.isdigit() else args.source

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Error: Unable to open video source {source}")
        return

    # Initialize Modules
    print(f"Loading YOLOv8 model from {args.model}...")
    detector = PersonDetector(model_path=args.model)
    print("YOLOv8 Loaded Initialized.")
    
    print("Initializing DeepSORT Tracking...")
    tracker = PersonTracker(max_age=30, n_init=3)

    # Variables for framerate calculation
    prev_time = 0

    # Retrieve width and height of video
    ret, frame = cap.read()
    if not ret:
        print("Error reading initial frame")
        return
    height, width, _ = frame.shape
    
    # Establish a virtual counting line across the middle of the frame
    line_y = int(height * 0.5)
    print(f"Initializing Counter across horizontal line Y={line_y}...")
    counter = PeopleCounter(line_y=line_y)

    print("\nStarting video pipeline. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Video stream ended or disconnected.")
            break

        # Calculate FPS
        current_time = time.time()
        fps_val = 1 / (current_time - prev_time) if prev_time > 0 else 0
        prev_time = current_time

        # 1. Detection
        detections = detector.detect(frame)

        # 2. Tracking
        tracked_objects = tracker.update(frame, detections)

        # 3. Counting (Updates counters and tracks history)
        current_visible_count = counter.update_and_count(tracked_objects)

        # Optional Drawing: Counter Line
        cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 2)
        cv2.putText(frame, "Counting Line", (10, line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        for track in tracked_objects:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            
            track_id = track.track_id
            x1, y1, x2, y2 = map(int, track.to_ltrb())
            
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # Draw Tracking BB and ID
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.circle(frame, (center_x, center_y), 4, (0, 255, 0), -1)

        # Display Metrics Display Panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 160), (0, 0, 0), -1)
        alpha = 0.5
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # HUD Text
        cv2.putText(frame, f"Tracking: {current_visible_count} People", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Total Entries: {counter.total_entries}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"Total Exits: {counter.total_exits}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"FPS: {fps_val:.1f}", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

        # Display Video Stream
        cv2.imshow("Real-Time People Counting Pipeline", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
