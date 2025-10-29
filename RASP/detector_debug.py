from ultralytics import YOLO
import cv2
import numpy as np
from config import Config


class FallDetector:
    """YOLO11 Fall Detection with visualization (DEBUG VERSION)"""
    
    def __init__(self):
        print(f"🤖 Loading YOLO11 model: {Config.YOLO_MODEL_PATH}")
        self.model = YOLO(Config.YOLO_MODEL_PATH)
        self.confidence_threshold = Config.CONFIDENCE_THRESHOLD
        self.aspect_ratio_threshold = Config.ASPECT_RATIO_THRESHOLD
        
        # 사람 감지용 낮은 임계값 (바운딩 박스 표시용)
        self.detection_threshold = 0.3  # 30%로 더 낮춤
        
        # Classes to detect for fall detection (COCO: person=0)
        self.fall_classes = [0]
        
        print(f"🔍 Detection Settings:")
        print(f"   Detection threshold (for bbox): {self.detection_threshold}")
        print(f"   Fall confidence threshold: {self.confidence_threshold}")
        print(f"   Aspect ratio threshold: {self.aspect_ratio_threshold}")
        
        self.frame_count = 0
        self.person_detected_count = 0
    
    def detect(self, frame, draw_boxes=True):
        """
        Fall detection with optional visualization
        
        Args:
            frame: Input frame
            draw_boxes: Whether to draw bounding boxes on the frame
        
        Returns:
            tuple: (detection_result, annotated_frame)
                - detection_result: dict or None (when a fall is detected)
                - annotated_frame: frame with bounding boxes drawn
        """
        self.frame_count += 1
        
        # Create a copy for drawing
        annotated_frame = frame.copy() if draw_boxes else frame
        
        # YOLO inference
        results = self.model(frame, verbose=False)
        
        fall_detected = None
        person_detected = False
        boxes_drawn = 0
        
        for result in results:
            boxes = result.boxes
            
            # 🔍 DEBUG: 감지된 객체 수
            if self.frame_count % 100 == 0 and len(boxes) > 0:
                print(f"\n🔍 YOLO Detection:")
                print(f"   Total objects detected: {len(boxes)}")
            
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                # 🔍 DEBUG: 모든 감지된 객체 출력
                if self.frame_count % 100 == 0:
                    class_name = self.model.names[cls]
                    print(f"   - Class: {class_name} (id={cls}), Confidence: {conf:.2f}")
                
                # 사람 클래스만 처리
                if cls in self.fall_classes:
                    # 매우 낮은 임계값으로 사람 감지
                    if conf > self.detection_threshold:
                        person_detected = True
                        self.person_detected_count += 1
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        
                        # Bounding box size
                        width = x2 - x1
                        height = y2 - y1
                        aspect_ratio = width / height if height > 0 else 0
                        
                        # Determine fall
                        is_fall = aspect_ratio > self.aspect_ratio_threshold
                        is_high_confidence_fall = is_fall and conf > self.confidence_threshold
                        
                        if draw_boxes:
                            boxes_drawn += 1
                            
                            # Color: Red for fall, Green for normal
                            color = (0, 0, 255) if is_fall else (0, 255, 0)
                            thickness = 3 if is_fall else 2
                            
                            # Draw bounding box
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)
                            
                            # Prepare label text
                            if is_fall:
                                label = f"FALL! ({conf:.2f})"
                            else:
                                label = f"Person ({conf:.2f})"
                            info = f"AR: {aspect_ratio:.2f}"
                            
                            # Font settings
                            font = cv2.FONT_HERSHEY_SIMPLEX
                            font_scale = 0.6
                            font_thickness = 2
                            
                            # Draw label background
                            (label_w, label_h), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
                            cv2.rectangle(annotated_frame, (x1, y1 - label_h - 10), (x1 + label_w + 10, y1), color, -1)
                            cv2.putText(annotated_frame, label, (x1 + 5, y1 - 5), font, font_scale, (255, 255, 255), font_thickness)
                            
                            # Draw info text below box
                            (info_w, info_h), _ = cv2.getTextSize(info, font, 0.5, 1)
                            cv2.rectangle(annotated_frame, (x1, y2), (x1 + info_w + 10, y2 + info_h + 5), color, -1)
                            cv2.putText(annotated_frame, info, (x1 + 5, y2 + info_h), font, 0.5, (255, 255, 255), 1)
                        
                        # Store fall detection result
                        if is_high_confidence_fall and fall_detected is None:
                            fall_detected = {
                                'detected': True,
                                'confidence': conf,
                                'bbox': (x1, y1, x2, y2),
                                'aspect_ratio': aspect_ratio
                            }
        
        # 🔍 DEBUG: 바운딩 박스 그리기 통계
        if self.frame_count % 100 == 0:
            print(f"\n🔍 Bounding Box Stats:")
            print(f"   Frames processed: {self.frame_count}")
            print(f"   Person detected: {self.person_detected_count} times")
            print(f"   Boxes drawn this frame: {boxes_drawn}")
        
        # Add status overlay
        if draw_boxes:
            # Status text
            if fall_detected:
                status_text = "🚨 FALL DETECTED!"
                status_color = (0, 0, 255)
            elif person_detected:
                status_text = "✓ Person Detected"
                status_color = (0, 255, 0)
            else:
                status_text = "○ Monitoring..."
                status_color = (200, 200, 200)
            
            # Draw status background
            cv2.rectangle(annotated_frame, (10, 10), (400, 50), (0, 0, 0), -1)
            cv2.rectangle(annotated_frame, (10, 10), (400, 50), status_color, 2)
            cv2.putText(annotated_frame, status_text, (20, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            
            # 🔍 DEBUG: 박스 개수 표시
            debug_text = f"Boxes: {boxes_drawn}"
            cv2.putText(annotated_frame, debug_text, (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return fall_detected, annotated_frame
