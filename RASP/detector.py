from ultralytics import YOLO
from config import Config


class FallDetector:
    """YOLO11 Fall Detection"""
    
    def __init__(self):
        print(f"🤖 Loading YOLO11 model: {Config.YOLO_MODEL_PATH}")
        self.model = YOLO(Config.YOLO_MODEL_PATH)
        self.confidence_threshold = Config.CONFIDENCE_THRESHOLD
        self.aspect_ratio_threshold = Config.ASPECT_RATIO_THRESHOLD
        
        # Classes to detect for fall detection (COCO: person=0)
        self.fall_classes = [0]
        
        print(f"🔍 Detection Settings:")
        print(f"   Confidence threshold: {self.confidence_threshold}")
        print(f"   Aspect ratio threshold: {self.aspect_ratio_threshold}")
    
    def detect(self, frame):
        """
        Fall detection
        
        Returns:
            dict or None: Detection result (when a fall is detected)
        """
        # YOLO inference
        results = self.model(frame, verbose=False)
        
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                # If the class is 'person' and confidence is high enough
                if cls in self.fall_classes and conf > self.confidence_threshold:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # Bounding box size
                    width = x2 - x1
                    height = y2 - y1
                    aspect_ratio = width / height if height > 0 else 0
                    
                    # Determine fall: width greater than height (lying posture)
                    if aspect_ratio > self.aspect_ratio_threshold:
                        return {
                            'detected': True,
                            'confidence': conf,
                            'bbox': (x1, y1, x2, y2),
                            'aspect_ratio': aspect_ratio
                        }
        
        return None

