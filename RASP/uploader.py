import requests
import cv2
from datetime import datetime, timezone  # ← timezone 추가
from config import Config


class BackendUploader:
    """Backend server communication"""
    
    def __init__(self):
        self.backend_url = Config.BACKEND_URL
        self.device_id = Config.DEVICE_ID
        
    def check_connection(self):
        """Check backend connection"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend connection successful")
                return True
            else:
                print(f"⚠️ Unexpected backend response: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend connection failed: {e}")
            return False
    
    def start_session(self):
        """Start streaming session"""
        try:
            response = requests.post(
                f"{self.backend_url}/api/stream/session/start",
                json={'device_id': self.device_id},
                timeout=5
            )
            
            if response.status_code == 200:
                print("✅ Streaming session started")
                return True
            else:
                print(f"⚠️ Failed to start session: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Session start error: {e}")
            return False
    
    def upload_frame(self, frame):
        """Upload frame"""
        try:
            # JPEG encoding
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()
            
            # Send frame
            files = {'frame': ('frame.jpg', frame_bytes, 'image/jpeg')}
            data = {'device_id': self.device_id}
            
            response = requests.post(
                f"{self.backend_url}/api/stream/upload",
                files=files,
                data=data,
                timeout=2
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def report_incident(self, detection_result):
        """Send fall incident signal"""
        try:
            incident_data = {
                'device_id': self.device_id,
                'incident_type': 'fall',
                'detected_at': datetime.now(timezone.utc).isoformat(),  # ← 수정
                'confidence': float(detection_result['confidence']),
                # CRITICAL FIX: User.id is String(50), not Integer
                'user_id': '1'  # Use the correct user ID
            }
            
            response = requests.post(
                f"{self.backend_url}/api/incidents/report",
                json=incident_data,
                timeout=10
            )
            
            if response.status_code == 201:
                print("✅ Fall incident reported successfully")
                return True
            else:
                print(f"⚠️ Failed to report incident: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Incident report error: {e}")
            return False
    
    def stop_session(self):
        """Stop streaming session"""
        try:
            requests.post(f"{self.backend_url}/api/stream/session/stop", timeout=5)
            print("✅ Streaming session stopped")
        except:
            pass