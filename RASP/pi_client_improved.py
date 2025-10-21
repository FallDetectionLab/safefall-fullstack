#!/usr/bin/env python3
"""
SafeFall Raspberry Pi client (최적화 + 안정성 개선)
"""

import time
import threading
from queue import Queue, Empty

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
            
    except KeyboardInterrupt:
        print("\nℹ️ Capture stopped")
    except Exception as e:
        print(f"❌ Capture thread error: {e}")


def streaming_thread(uploader):
    """Streaming upload thread"""
    global running
    
    frame_count = 0
    error_count = 0
    start_time = time.time()
    
    try:
        while running:
            if frame_queue.empty():
                time.sleep(0.001)
                continue
            
            try:
                frame = frame_queue.get(timeout=1)
                
                if uploader.upload_frame(frame):
                    frame_count += 1
                    error_count = 0  # 성공 시 에러 카운트 리셋
                    
                    if frame_count % 100 == 0:
                        elapsed = time.time() - start_time
                        actual_fps = frame_count / elapsed
                        print(f"📡 Upload: {frame_count} frames ({actual_fps:.2f} fps)")
                else:
                    error_count += 1
                    if error_count >= 10:  # 10회 연속 실패 시 경고
                        print(f"⚠️ Upload failed {error_count} times consecutively")
                        error_count = 0  # 경고 후 리셋
                        
            except Empty:
                continue
            except Exception as e:
                error_count += 1
                if error_count % 100 == 0:  # 너무 자주 출력 방지
                    print(f"⚠️ Upload error: {e}")
            
    except KeyboardInterrupt:
        print("\nℹ️ Streaming stopped")


def detection_thread(detector, uploader):
    """Detection thread (개선된 버전)"""
    global running
    
    last_detection_time = 0
    cooldown = 5  # 5 seconds cooldown
    detection_buffer = None
    
    try:
        while running:
            # 큐에서 최신 프레임 가져오기 (논블로킹)
            if not frame_queue.empty():
                try:
                    detection_buffer = frame_queue.get(block=False)
                except Empty:
                    pass
            
            if detection_buffer is None:
                time.sleep(0.1)
                continue
            
            try:
                # Fall detection
                result = detector.detect(detection_buffer)
                
                if result and result.get('detected'):
                    current_time = time.time()
                    
                    # Cooldown check
                    if current_time - last_detection_time > cooldown:
                        confidence = result.get('confidence', 0)
                        print(f"🚨 Fall detected! Confidence: {confidence:.2f}")
                        
                        # Send incident signal
                        uploader.report_incident(result)
                        
                        last_detection_time = current_time
                        time.sleep(cooldown)
                        
            except Exception as e:
                print(f"⚠️ Detection error: {e}")
            
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
    try:
        camera = RPiCamera()
        detector = FallDetector()
        uploader = BackendUploader()
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        return
    
    # Check backend connection
    if not uploader.check_connection():
        print("❌ Failed to connect to backend server. Exiting.")
        return
    
    # Start session
    if not uploader.start_session():
        print("⚠️ Failed to start session, but continuing...")
    
    # Start camera
    try:
        camera.start()
    except Exception as e:
        print(f"❌ Failed to start camera: {e}")
        return
    
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
    
    print("\n💡 Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        while running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutdown signal received")
        running = False
        
        # Cleanup
        print("🧹 Cleaning up...")
        
        # 1. 카메라 먼저 정지
        try:
            camera.stop()
            print("✅ Camera stopped")
        except Exception as e:
            print(f"⚠️ Camera stop error: {e}")
        
        # 2. 세션 종료
        try:
            uploader.stop_session()
            print("✅ Session stopped")
        except Exception as e:
            print(f"⚠️ Session stop error: {e}")
        
        # 3. 스레드 종료 대기
        for t in threads:
            print(f"⏳ Waiting for {t.name} thread...")
            t.join(timeout=3)
            if t.is_alive():
                print(f"⚠️ {t.name} thread still running")
            else:
                print(f"✅ {t.name} thread stopped")
        
        print("=" * 60)
        print("👋 SafeFall client stopped gracefully")
        print("=" * 60)


if __name__ == '__main__':
    main()
