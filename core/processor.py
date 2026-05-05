import cv2
import numpy as np
from ultralytics import YOLO

class VideoProcessor:
    def __init__(self, model_path=r'weights/yolov8n.pt'):
        """
        Initializes the YOLOv8-Nano model for high-efficiency inference.
        """
        try:
            self.model = YOLO(model_path)
        except Exception:
            self.model = YOLO('yolov8n.pt') 
            
        self.count_history = set() 

    def apply_honey_blur(self, frame, boxes):
        """
        Applies a heavy Gaussian Blur to detected ROI for privacy compliance.
        """
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
            
            roi = frame[y1:y2, x1:x2]
            if roi.size > 0:
                blur_roi = cv2.GaussianBlur(roi, (51, 51), 0)
                frame[y1:y2, x1:x2] = blur_roi
        return frame

    def process_frame(self, frame, enable_blur=True):
        """
        Executes YOLOv8 tracking with ByteTrack persistence.
        """
        results = self.model.track(
            source=frame, 
            persist=True, 
            tracker="bytetrack.yaml", 
            verbose=False
        )
        
        annotated_frame = frame.copy()
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
            
            for tid in track_ids:
                self.count_history.add(tid)
            
            if enable_blur:
                annotated_frame = self.apply_honey_blur(annotated_frame, boxes)
            
            # Plotting the F1-style labels over the blurred regions
            annotated_frame = results[0].plot(img=annotated_frame)

        return annotated_frame, len(self.count_history)