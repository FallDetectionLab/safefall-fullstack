#!/usr/bin/env python3
"""
SafeFall Raspberry Pi client (디버깅 버전)
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
annotated_frame_queue = Queue(maxsize=30)
running = True


def capture_thread(camera):
    """Camera capture thread"""
    global running
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while running:
            frame = camera.read_frame()
            
            if frame is None:
                time.sleep(0.001)
                continue
            
            if not frame_queue.full():
                frame_queue.put(frame)
                frame_count += 1
                
                if frame_count % 300 == 0:
                    elapsed = time.time() - start_time
                    actual_fps = frame_count / elapsed
                    print(f"📊 Capture FPS: {actual_fps:.2f} ({frame_count} frames)")
            
    except KeyboardInterrupt:
        print("\nℹ️ Capture stopped")
    except Exception as e:
        print(f"❌ Capture thread error: {e}")


def detection_thread(detector):
    """Detection and annotation thread with DEBUG logging"""
    global running
    
    last_detection_time = 0
    frame_count = 0
    person_detected_count = 0
    fall_detected_count = 0
    
    try:
        while running:
            if frame_queue.empty():
                time.sleep(0.01)
                continue
            
            try:
                frame = frame_queue.get(block=False)
                frame_count += 1
            except Empty:
                time.sleep(0.01)
                continue
            
            try:
                # 🔍 DEBUG: Fall detection with bounding boxes
                result, annotated_frame = detector.detect(frame, draw_boxes=True)
                
                # 🔍 DEBUG: 프레임 정보 출력
                if frame_count % 100 == 0:
                    print(f"\n🔍 DEBUG - Detection Thread:")
                    print(f"   Processed frames: {frame_count}")
                    print(f"   Person detected: {person_detected_count} times")
                    print(f"   Fall detected: {fall_detected_count} times")
                    print(f"   Annotated queue size: {annotated_frame_queue.qsize()}")
                
                # 🔍 DEBUG: 감지 결과 확인
                if result:
                    person_detected_count += 1
                    if result.get('detected'):
                        fall_detected_count += 1
                
                # 바운딩 박스 그려진 프레임을 업로드용 큐에 추가
                if not annotated_frame_queue.full():
                    annotated_frame_queue.put(annotated_frame)
                else:
                    # 큐가 가득 차면 오래된 프레임 제거 후 추가
                    try:
                        annotated_frame_queue.get(block=False)
                    except:
                        pass
                    annotated_frame_queue.put(annotated_frame)
                
                # 낙상 감지 시 로그
                if result and result.get('detected'):
                    current_time = time.time()
                    if current_time - last_detection_time > 5:
                        confidence = result.get('confidence', 0)
                        aspect_ratio = result.get('aspect_ratio', 0)
                        print(f"\n🚨 FALL DETECTED!")
                        print(f"   Confidence: {confidence:.2f}")
                        print(f"   Aspect Ratio: {aspect_ratio:.2f}")
                        last_detection_time = current_time
                
            except Exception as e:
                print(f"⚠️ Detection error: {e}")
                import traceback
                traceback.print_exc()
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nℹ️ Detection stopped")


def streaming_thread(uploader):
    """Streaming upload thread with DEBUG logging"""
    global running
    
    frame_count = 0
    error_count = 0
    start_time = time.time()
    
    try:
        while running:
            if annotated_frame_queue.empty():
                time.sleep(0.001)
                continue
            
            try:
                # 바운딩 박스가 그려진 프레임 가져오기
                annotated_frame = annotated_frame_queue.get(timeout=1)
                
                # 🔍 DEBUG: 프레임 정보
                if frame_count == 0:
                    print(f"\n🔍 DEBUG - First Frame Upload:")
                    print(f"   Frame shape: {annotated_frame.shape}")
                    print(f"   Frame dtype: {annotated_frame.dtype}")
                
                # 백엔드로 업로드
                if uploader.upload_frame(annotated_frame):
                    frame_count += 1
                    error_count = 0
                    
                    if frame_count % 100 == 0:
                        elapsed = time.time() - start_time
                        actual_fps = frame_count / elapsed
                        print(f"\n📡 Upload Stats:")
                        print(f"   Frames uploaded: {frame_count}")
                        print(f"   Upload FPS: {actual_fps:.2f}")
                else:
                    error_count += 1
                    if error_count >= 10:
                        print(f"⚠️ Upload failed {error_count} times consecutively")
                        error_count = 0
                        
            except Empty:
                continue
            except Exception as e:
                error_count += 1
                if error_count % 100 == 0:
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
        window_name = "SafeFall - Fall Detection [DEBUG]"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1280, 720)
        window_created = True
        print("🖥️ Display window opened")
        print("   Press ESC to quit")
    except Exception as e:
        print(f"⚠️ Failed to create display window: {e}")
        print("   Continuing without local display...")
        return
    
    display_frame_count = 0
    
    try:
        while running:
            if annotated_frame_queue.empty():
                time.sleep(0.01)
                continue
            
            try:
                # 큐에서 최신 프레임만 가져오기
                annotated_frame = None
                while not annotated_frame_queue.empty():
                    try:
                        annotated_frame = annotated_frame_queue.get(block=False)
                    except Empty:
                        break
                
                if annotated_frame is not None:
                    display_frame_count += 1
                    
                    # 🔍 DEBUG: 프레임 카운터 추가
                    cv2.putText(
                        annotated_frame,
                        f"Frame: {display_frame_count}",
                        (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1
                    )
                    
                    cv2.imshow(window_name, annotated_frame)
                
                # ESC 키 확인
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
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


def incident_reporting_thread(uploader, detector):
    """Incident reporting thread"""
    global running
    
    last_detection_time = 0
    cooldown = 5
    
    try:
        while running:
            if frame_queue.empty():
                time.sleep(0.1)
                continue
            
            try:
                frame = frame_queue.queue[-1] if len(frame_queue.queue) > 0 else None
            except:
                frame = None
            
            if frame is None:
                time.sleep(0.1)
                continue
            
            try:
                # 낙상 감지
                result, _ = detector.detect(frame, draw_boxes=False)
                
                if result and result.get('detected'):
                    current_time = time.time()
                    
                    if current_time - last_detection_time > cooldown:
                        print(f"\n📤 Reporting incident to backend...")
                        if uploader.report_incident(result):
                            print(f"✅ Incident reported successfully")
                        else:
                            print(f"❌ Failed to report incident")
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
    print("🚀 SafeFall Raspberry Pi client starting [DEBUG MODE]")
    print("=" * 60)
    
    # Initialize configuration
    Config.init()
    
    print(f"\n🔍 DEBUG - Configuration:")
    print(f"   Backend URL: {Config.BACKEND_URL}")
    print(f"   Device ID: {Config.DEVICE_ID}")
    print(f"   Display enabled: {Config.ENABLE_DISPLAY}")
    print(f"   Detection threshold: 0.5 (for bounding boxes)")
    print(f"   Fall threshold: {Config.CONFIDENCE_THRESHOLD}")
    
    # Initialize components
    try:
        camera = RPiCamera()
        detector = FallDetector()
        uploader = BackendUploader()
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        import traceback
        traceback.print_exc()
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
        threading.Thread(target=incident_reporting_thread, args=(uploader, detector), name="IncidentReport"),
    ]
    
    for t in threads:
        t.daemon = True
        t.start()
        print(f"✅ {t.name} thread started")
    
    print("\n" + "=" * 60)
    if Config.ENABLE_DISPLAY:
        print("💡 Controls:")
        print("   - Press ESC in the display window to quit")
        print("   - Or press Ctrl+C in terminal")
    else:
        print("💡 Running in headless mode")
        print("   - Press Ctrl+C to quit")
    
    print("\n📡 Check if bounding boxes appear in:")
    print("   1. Local display (if ENABLE_DISPLAY=true)")
    print("   2. Frontend dashboard")
    print("=" * 60 + "\n")
    
    try:
        while running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutdown signal received")
        running = False
        
        # Cleanup
        print("🧹 Cleaning up...")
        
        try:
            cv2.destroyAllWindows()
            print("✅ Display windows closed")
        except:
            pass
        
        try:
            camera.stop()
            print("✅ Camera stopped")
        except Exception as e:
            print(f"⚠️ Camera stop error: {e}")
        
        try:
            uploader.stop_session()
            print("✅ Session stopped")
        except Exception as e:
            print(f"⚠️ Session stop error: {e}")
        
        for t in threads:
            t.join(timeout=2)
        
        print("=" * 60)
        print("👋 SafeFall client stopped")
        print("=" * 60)


if __name__ == '__main__':
    main()
