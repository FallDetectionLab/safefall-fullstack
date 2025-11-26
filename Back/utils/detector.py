"""
YOLO11 Pose-based Fall Detection for Backend
Migrated from Raspberry Pi client
"""
from ultralytics import YOLO
import cv2
import numpy as np
from config import Config


class FallDetector:
    """YOLO11 Fall Detection with visualization"""

    def __init__(self):
        """Initialize YOLO11 Pose model"""
        model_path = Config.YOLO_MODEL_PATH
        print(f"🤖 Loading YOLO11 Pose model: {model_path}")

        try:
            self.model = YOLO(model_path)
            print(f"✅ YOLO11 model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            raise

        self.confidence_threshold = Config.CONFIDENCE_THRESHOLD
        self.aspect_ratio_threshold = Config.ASPECT_RATIO_THRESHOLD

        # 사람 감지용 낮은 임계값 (바운딩 박스 표시용)
        self.detection_threshold = 0.5  # 50% 이상이면 바운딩 박스 표시

        # Classes to detect for fall detection (COCO: person=0)
        self.fall_classes = [0]

        print(f"🔍 Detection Settings:")
        print(f"   Detection threshold (for bbox): {self.detection_threshold}")
        print(f"   Fall confidence threshold: {self.confidence_threshold}")
        print(f"   Aspect ratio threshold: {self.aspect_ratio_threshold}")

    def detect(self, frame, draw_boxes=True):
        """
        Fall detection with optional visualization

        Args:
            frame: Input frame (numpy array)
            draw_boxes: Whether to draw bounding boxes on the frame

        Returns:
            tuple: (detection_result, annotated_frame)
                - detection_result: dict or None (when a fall is detected)
                - annotated_frame: frame with bounding boxes drawn
        """
        # Create a copy for drawing
        annotated_frame = frame.copy() if draw_boxes else frame

        # YOLO inference
        results = self.model(frame, verbose=False)

        fall_detected = None
        person_detected = False

        for result in results:
            boxes = result.boxes

            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                # 사람 클래스만 처리
                if cls in self.fall_classes:
                    # 낮은 임계값으로 사람 감지 (바운딩 박스 표시용)
                    if conf > self.detection_threshold:
                        person_detected = True
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())

                        # Bounding box size
                        width = x2 - x1
                        height = y2 - y1
                        aspect_ratio = width / height if height > 0 else 0

                        # Determine fall: width greater than height (lying posture)
                        is_fall = aspect_ratio > self.aspect_ratio_threshold

                        # 낙상 판단은 높은 임계값 적용
                        is_high_confidence_fall = is_fall and conf > self.confidence_threshold

                        if draw_boxes:
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

                            # Calculate text size for background
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

                        # Store fall detection result (높은 신뢰도 낙상만 보고)
                        if is_high_confidence_fall and fall_detected is None:
                            fall_detected = {
                                'detected': True,
                                'confidence': conf,
                                'bbox': (x1, y1, x2, y2),
                                'aspect_ratio': aspect_ratio
                            }

        # Add FPS and status overlay
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
            cv2.rectangle(annotated_frame, (10, 10), (350, 50), (0, 0, 0), -1)
            cv2.rectangle(annotated_frame, (10, 10), (350, 50), status_color, 2)
            cv2.putText(annotated_frame, status_text, (20, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        return fall_detected, annotated_frame
