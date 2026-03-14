import cv2
import math
from ultralytics import YOLO

class PersonDetector:
    """
    Detector class using Ultralytics YOLOv8.
    It returns detections in the format required by DeepSORT.
    """
    def __init__(self, model_path="yolov8n.pt"):
        # Load the lightweight YOLOv8 nano model for fast real-time inference
        self.model = YOLO(model_path)
        self.class_id = 0 # COCO dataset class ID for 'person'

    def detect(self, frame):
        """
        Detects people in a given frame.

        Args:
            frame: A numpy array representing the image frame (BGR from OpenCV).

        Returns:
            A list of detections. Each detection is a tuple: 
            ([x, y, w, h], confidence, class_name)
        """
        # Run YOLOv8 inference
        # classes=[0] restricts it to detecting only people
        # conf=0.5 sets a confidence threshold to filter out weak detections
        results = self.model.predict(source=frame, classes=[self.class_id], conf=0.5, verbose=False)

        detections = []
        for result in results:
            for box in result.boxes:
                # Extract bounding box mapping to [x1, y1, width, height]
                x_center, y_center, width, height = box.xywh[0].cpu().numpy()
                x1 = x_center - (width / 2)
                y1 = y_center - (height / 2)
                
                conf = math.ceil((box.conf[0].cpu().item() * 100)) / 100
                
                # Append to detections list
                detections.append(([x1, y1, width, height], conf, 'person'))

        return detections
