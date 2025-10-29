#!/usr/bin/env python3
"""
SafeFall Raspberry Pi client (최적화 + 화면 표시)
바운딩 박스가 라즈베리파이 로컬 화면 + 프론트엔드 대시보드 모두에 표시됨
"""

import time
import threading
import cv2
from queue import Queue, Empty

from config import Config
from camera import RPiCamera
from detector import FallDetector
from uploader import BackendUploader


# Global variables
frame_queue = Queue(maxsize=100)
annotated_frame_queue = Queue(maxsize=30)  # 바운딩 박스 그려진 프레임
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


def detection_thread(detector):
    """Detection and annotation thread - 바운딩 박스 그리기"""
    global running
    
    last_detection_time = 0
    detection_result = None
    
    try:
        while running:
            if frame_queue.empty():
                time.sleep(0.01)
                continue
            
            try:
                frame = frame_queue.get(block=False)
            except Empty:
                time.sleep(0.01)
                continue
            
            try:
                # Fall detection with bounding boxes (항상 바운딩 박스 그림)
                result, annotated_frame = detector.detect(frame, draw_boxes=True)
                
                # 바운딩 박스 그려진 프레임을 업로드용 큐에 추가
                if not annotated_frame_queue.full():
                    annotated_frame_queue.put(annotated_frame)
                
                # 낙상 감지 결과 저장
                if result and result.get('detected'):
                    current_time = time.time()
                    if current_time - last_detection_time > 5:  # 5초 cooldown
                        detection_result = result
                        last_detection_time = current_time
                        
                        confidence = result.get('confidence', 0)
                        aspect_ratio = result.get('aspect_ratio', 0)
                        print(f"🚨 Fall detected! Confidence: {confidence:.2f}, AR: {aspect_ratio:.2f}")
                
            except Exception as e:
                print(f"⚠️ Detection error: {e}")
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nℹ️ Detection stopped")


def streaming_thread(uploader):
    """Streaming upload thread - 바운딩 박스 그려진 프레임 업로드"""
    global running
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while running:
            if annotated_frame_queue.empty():
                time.sleep(0.001)
                continue
            
            try:
                # 바운딩 박스가 그려진 프레임 가져오기
                annotated_frame = annotated_frame_queue.get(timeout=1)
                
                # 백엔드로 업로드 (프론트엔드에 바운딩 박스 표시됨)
                if uploader.upload_frame(annotated_frame):
                    frame_count += 1
                    if frame_count % 100 == 0:
                        elapsed = time.time() - start_time
                        actual_fps = frame_count / elapsed
                        print(f"📡 Upload: {frame_count} frames ({actual_fps:.2f} fps)")
                        
            except Empty:
                continue
            except Exception as e:
                if frame_count % 100 == 0:
                    print(f"⚠️ Upload error: {e}")
            
    except KeyboardInterrupt:
        print("\nℹ️ Streaming stopped")


def display_thread():
    """Display thread - 라즈베리파이 로컬 화면 표시"""
    global running
    
    if not Config.ENABLE_DISPLAY:
        print("🖥️ Display disabled (headless mode)")
        return
    
    window_created = False
    try:
        window_name = "SafeFall - Fall Detection"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1280, 720)
        window_created = True
        print("🖥️ Display window opened")
        print("   Press ESC to quit")
    except Exception as e:
        print(f"⚠️ Failed to create display window: {e}")
        print("   Continuing without local display...")
        return
    
    try:
        while running:
            if annotated_frame_queue.empty():
                time.sleep(0.01)
                continue
            
            try:
                # 바운딩 박스가 그려진 프레임 가져오기 (복사본)
                # 큐에서 가장 최신 프레임만 가져오기
                annotated_frame = None
                while not annotated_frame_queue.empty():
                    try:
                        annotated_frame = annotated_frame_queue.get(block=False)
                    except Empty:
                        break
                
                if annotated_frame is not None:
                    cv2.imshow(window_name, annotated_frame)
                
                # ESC 키 확인
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC key
                    print("\n🛑 ESC pressed - stopping...")
                    running = False
                    break
                    
            except Exception as e:
                print(f"⚠️ Display error: {e}")
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nℹ️ Display stopped")
    finally:
        if window_created:
            cv2.destroyAllWindows()
            print("🖥️ Display window closed")


def incident_reporting_thread(uploader):
    """Incident reporting thread - 낙상 감지 시 백엔드에 알림"""
    global running
    
    last_detection_time = 0
    cooldown = 5
    
    try:
        while running:
            if frame_queue.empty():
                time.sleep(0.1)
                continue
            
            # 큐에서 최신 프레임 확인
            try:
                frame = frame_queue.queue[-1] if len(frame_queue.queue) > 0 else None
            except:
                frame = None
            
            if frame is None:
                time.sleep(0.1)
                continue
            
            try:
                # 낙상 감지 (바운딩 박스 그리지 않음)
                result, _ = detector.detect(frame, draw_boxes=False)
                
                if result and result.get('detected'):
                    current_time = time.time()
                    
                    if current_time - last_detection_time > cooldown:
                        # 백엔드에 사고 알림
                        uploader.report_incident(result)
                        last_detection_time = current_time
                        time.sleep(cooldown)
                        
            except Exception as e:
                print(f"⚠️ Incident reporting error: {e}")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nℹ️ Incident reporting stopped")


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
        global detector
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
        threading.Thread(target=detection_thread, args=(detector,), name="Detection"),
        threading.Thread(target=streaming_thread, args=(uploader,), name="Streaming"),
        threading.Thread(target=display_thread, name="Display"),
        threading.Thread(target=incident_reporting_thread, args=(uploader,), name="IncidentReport"),
    ]
    
    for t in threads:
        t.daemon = True
        t.start()
        print(f"✅ {t.name} thread started")
    
    if Config.ENABLE_DISPLAY:
        print("\n💡 Controls:")
        print("   - Press ESC in the display window to quit")
        print("   - Or press Ctrl+C in terminal")
    else:
        print("\n💡 Running in headless mode (no local display)")
        print("   - Press Ctrl+C to quit")
    
    print("\n📡 Frontend dashboard will show bounding boxes in real-time")
    print("=" * 60)
    
    try:
        while running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutdown signal received")
        running = False
        
        # Cleanup
        print("🧹 Cleaning up...")
        
        # 1. OpenCV 창 닫기
        try:
            cv2.destroyAllWindows()
            print("✅ Display windows closed")
        except:
            pass
        
        # 2. 카메라 정지
        try:
            camera.stop()
            print("✅ Camera stopped")
        except Exception as e:
            print(f"⚠️ Camera stop error: {e}")
        
        # 3. 세션 종료
        try:
            uploader.stop_session()
            print("✅ Session stopped")
        except Exception as e:
            print(f"⚠️ Session stop error: {e}")
        
        # 4. 스레드 종료 대기
        for t in threads:
            t.join(timeout=2)
        
        print("=" * 60)
        print("👋 SafeFall client stopped")
        print("=" * 60)


if __name__ == '__main__':
    main()
