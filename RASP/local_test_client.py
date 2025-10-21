#!/usr/bin/env python3
"""
로컬 개발용 더미 카메라 클라이언트
웹캠이나 테스트 이미지를 사용하여 백엔드로 스트리밍
"""

import cv2
import time
import requests
import threading
from datetime import datetime, timezone


class LocalTestClient:
    def __init__(self, backend_url="http://localhost:5000", device_id="local-test"):
        self.backend_url = backend_url
        self.device_id = device_id
        self.running = False
        
    def check_connection(self):
        """백엔드 연결 확인"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend connection successful")
                return True
            else:
                print(f"⚠️ Backend response: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend connection failed: {e}")
            return False
    
    def start_session(self):
        """스트리밍 세션 시작"""
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
        """프레임 업로드"""
        try:
            # JPEG 인코딩
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()
            
            # 프레임 전송
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
    
    def stop_session(self):
        """세션 종료"""
        try:
            requests.post(f"{self.backend_url}/api/stream/session/stop", timeout=5)
            print("✅ Session stopped")
        except:
            pass
    
    def start_webcam_streaming(self):
        """웹캠 스트리밍 시작"""
        print("🎥 Starting webcam streaming...")
        
        # 웹캠 초기화 (0은 기본 카메라)
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot open webcam")
            return
        
        # 해상도 설정
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)
        
        frame_count = 0
        start_time = time.time()
        
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    print("⚠️ Failed to read frame")
                    continue
                
                # 프레임 업로드
                if self.upload_frame(frame):
                    frame_count += 1
                    
                    # 10초마다 상태 출력
                    if frame_count % 150 == 0:  # 15fps * 10초
                        elapsed = time.time() - start_time
                        fps = frame_count / elapsed
                        print(f"📡 Uploaded {frame_count} frames ({fps:.1f} fps)")
                
                # FPS 제어 (15fps)
                time.sleep(1/15)
                
        except KeyboardInterrupt:
            print("\n🛑 Streaming stopped by user")
        finally:
            cap.release()
            print("📹 Webcam released")
    
    def start(self):
        """메인 실행 함수"""
        print("=" * 60)
        print("🖥️ SafeFall Local Test Client")
        print(f"   Backend: {self.backend_url}")
        print(f"   Device: {self.device_id}")
        print("=" * 60)
        
        # 백엔드 연결 확인
        if not self.check_connection():
            print("❌ Cannot connect to backend. Make sure it's running!")
            return
        
        # 세션 시작
        if not self.start_session():
            print("⚠️ Failed to start session, but continuing...")
        
        # 스트리밍 시작
        self.running = True
        
        try:
            self.start_webcam_streaming()
        finally:
            self.running = False
            self.stop_session()
            print("👋 Local test client stopped")


if __name__ == '__main__':
    client = LocalTestClient()
    client.start()