#!/usr/bin/env python3
"""
SafeFall Raspberry Pi client (경량 버전 - YOLO 처리 백엔드 이전)
원본 프레임만 백엔드로 전송하고, 백엔드에서 YOLO 처리 수행
"""

import time
import threading
import cv2
from queue import Queue, Empty

from config import Config
from camera import RPiCamera
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
    """Streaming upload thread - 원본 프레임 업로드 (백엔드에서 YOLO 처리)"""
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
                # 원본 프레임 가져오기
                frame = frame_queue.get(timeout=1)

                # 백엔드로 업로드 (백엔드에서 YOLO 처리됨)
                if uploader.upload_frame(frame):
                    frame_count += 1
                    error_count = 0

                    if frame_count % 100 == 0:
                        elapsed = time.time() - start_time
                        actual_fps = frame_count / elapsed
                        print(f"📡 Upload: {frame_count} frames ({actual_fps:.2f} fps)")
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
    """Display thread - 원본 프레임 로컬 화면 표시"""
    global running

    if not Config.ENABLE_DISPLAY:
        print("🖥️ Display disabled (headless mode)")
        return

    window_created = False
    try:
        window_name = "SafeFall - Camera Feed"
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
            if frame_queue.empty():
                time.sleep(0.01)
                continue

            try:
                # 원본 프레임 가져오기 (가장 최신 프레임)
                current_frame = None
                while not frame_queue.empty():
                    try:
                        current_frame = frame_queue.get(block=False)
                    except Empty:
                        break

                if current_frame is not None:
                    cv2.imshow(window_name, current_frame)

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


def main():
    """Main function"""
    global running

    print("=" * 60)
    print("🚀 SafeFall Raspberry Pi client starting (경량 버전)")
    print("   YOLO 처리는 백엔드에서 수행됩니다")
    print("=" * 60)

    # Initialize configuration
    Config.init()

    # Initialize components
    try:
        camera = RPiCamera()
        uploader = BackendUploader()
        print("✅ Components initialized (Camera, Uploader)")
        print("   ⚡ YOLO 모델 로드 안 함 (백엔드에서 처리)")
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

    # Start threads (Detection, IncidentReport 제거)
    threads = [
        threading.Thread(target=capture_thread, args=(camera,), name="Capture"),
        threading.Thread(target=streaming_thread, args=(uploader,), name="Streaming"),
        threading.Thread(target=display_thread, name="Display"),
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

    print("\n📡 원본 프레임을 백엔드로 전송 중...")
    print("🎯 낙상 감지 및 바운딩 박스는 백엔드에서 처리됩니다")
    print("📺 프론트엔드 대시보드에서 YOLO 처리된 영상을 확인하세요")
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
