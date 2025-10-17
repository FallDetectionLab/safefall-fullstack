#!/usr/bin/env python3
"""
SafeFall Raspberry Pi client (최적화)
"""

import time
import threading
from queue import Queue

from config import Config
from camera import RPiCamera
from detector import FallDetector
from uploader import BackendUploader


# Global variables
frame_queue = Queue(maxsize=100)
running = True


def capture_thread(camera):
    """Camera capture thread (최적화)"""
    global running
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while running:
            frame = camera.read_frame()
            
            if frame is None:
                time.sleep(0.001)  # 1ms만 대기
                continue
            
            if not frame_queue.full():
                frame_queue.put(frame)
                frame_count += 1
                
                # 10초마다 실제 FPS 출력
                if frame_count % 300 == 0:
                    elapsed = time.time() - start_time
                    actual_fps = frame_count / elapsed
                    print(f"📊 Capture FPS: {actual_fps:.2f} ({frame_count} frames / {elapsed:.2f}s)")
            
            # FPS 제어 제거 - 카메라가 자체적으로 FPS 조절
            # time.sleep(1/Config.CAMERA_FPS)  # 이 줄 제거!
            
    except KeyboardInterrupt:
        print("\nℹ️ Capture stopped")


def streaming_thread(uploader):
    """Streaming upload thread"""
    global running
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while running:
            if frame_queue.empty():
                time.sleep(0.001)
                continue
            
            frame = frame_queue.get()
            
            if uploader.upload_frame(frame):
                frame_count += 1
                if frame_count % 100 == 0:
                    elapsed = time.time() - start_time
                    actual_fps = frame_count / elapsed
                    print(f"📡 Upload: {frame_count} frames ({actual_fps:.2f} fps)")
            
    except KeyboardInterrupt:
        print("\nℹ️ Streaming stopped")


def detection_thread(detector, uploader):
    """Detection thread"""
    global running
    
    last_detection_time = 0
    cooldown = 5  # 5 seconds cooldown
    
    try:
        while running:
            if frame_queue.empty():
                time.sleep(0.1)
                continue
            
            # 큐에서 프레임 복사 (원본 유지)
            frame = frame_queue.queue[0] if len(frame_queue.queue) > 0 else None
            
            if frame is None:
                time.sleep(0.1)
                continue
            
            # Fall detection
            result = detector.detect(frame)
            
            if result and result['detected']:
                current_time = time.time()
                
                # Cooldown check
                if current_time - last_detection_time > cooldown:
                    print(f"🚨 Fall detected! Confidence: {result['confidence']:.2f}")
                    
                    # Send incident signal
                    uploader.report_incident(result)
                    
                    last_detection_time = current_time
                    time.sleep(cooldown)
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nℹ️ Detection stopped")


def main():
    """Main function"""
    global running
    
    print("=" * 60)
    print("🚀 SafeFall Raspberry Pi client starting")
    print("=" * 60)
    
    # Initialize configuration
    Config.init()
    
    # Initialize components
    camera = RPiCamera()
    detector = FallDetector()
    uploader = BackendUploader()
    
    # Check backend connection
    if not uploader.check_connection():
        print("Failed to connect to backend server. Exiting.")
        return
    
    # Start session
    uploader.start_session()
    
    # Start camera
    camera.start()
    
    # Start threads
    threads = [
        threading.Thread(target=capture_thread, args=(camera,), name="Capture"),
        threading.Thread(target=streaming_thread, args=(uploader,), name="Streaming"),
        threading.Thread(target=detection_thread, args=(detector, uploader), name="Detection"),
    ]
    
    for t in threads:
        t.daemon = True
        t.start()
        print(f"✅ {t.name} thread started")
    
    try:
        while running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutdown signal received")
        running = False
        
        # Cleanup
        camera.stop()
        uploader.stop_session()
        
        for t in threads:
            t.join(timeout=2)
        
        print("👋 SafeFall client stopped")


if __name__ == '__main__':
    main()