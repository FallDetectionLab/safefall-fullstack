import subprocess
import numpy as np
import cv2
from config import Config


class RPiCamera:
    """Raspberry Pi camera capture (최적화)"""
    
    def __init__(self):
        self.width = Config.CAMERA_WIDTH
        self.height = Config.CAMERA_HEIGHT
        self.fps = Config.CAMERA_FPS
        self.process = None
        self.buffer = b''
        
    def start(self):
        """Start MJPEG streaming with rpicam-vid"""
        cmd = [
            'rpicam-vid',
            '--width', str(self.width),
            '--height', str(self.height),
            '--framerate', str(self.fps),
            '--codec', 'mjpeg',
            '--output', '-',
            '--timeout', '0',
            '--nopreview'
        ]
        
        print(f"📹 Camera started: {self.width}x{self.height} @ {self.fps}fps")
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=10**8
        )
        
        return self
    
    def read_frame(self):
        """
        Read frame (최적화된 MJPEG 파싱)
        청크 단위로 읽어서 성능 개선
        """
        if not self.process:
            return None
        
        try:
            chunk_size = 4096  # 4KB씩 읽기
            
            # JPEG 시작 마커 찾기 (0xFFD8)
            while True:
                if len(self.buffer) < 2:
                    chunk = self.process.stdout.read(chunk_size)
                    if not chunk:
                        return None
                    self.buffer += chunk
                
                # 시작 마커 찾기
                start_idx = self.buffer.find(b'\xff\xd8')
                if start_idx != -1:
                    self.buffer = self.buffer[start_idx:]
                    break
                else:
                    # 마지막 1바이트만 남기고 버림 (마커가 경계에 걸칠 수 있음)
                    self.buffer = self.buffer[-1:]
            
            # JPEG 끝 마커 찾기 (0xFFD9)
            while True:
                end_idx = self.buffer.find(b'\xff\xd9')
                if end_idx != -1:
                    # 완전한 JPEG 프레임 추출
                    jpeg_data = self.buffer[:end_idx + 2]
                    self.buffer = self.buffer[end_idx + 2:]
                    
                    # 디코딩
                    nparr = np.frombuffer(jpeg_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        return frame
                    else:
                        # 디코딩 실패, 다음 프레임 시도
                        continue
                else:
                    # 더 읽기
                    chunk = self.process.stdout.read(chunk_size)
                    if not chunk:
                        return None
                    self.buffer += chunk
                    
                    # 버퍼가 너무 커지면 잘라냄 (메모리 보호)
                    if len(self.buffer) > 1024 * 1024:  # 1MB 초과
                        print("⚠️ Buffer overflow, resetting")
                        self.buffer = b''
                        return None
                    
        except Exception as e:
            print(f"❌ Failed to read frame: {e}")
            return None
    
    def stop(self):
        """Stop camera"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("Camera stopped")