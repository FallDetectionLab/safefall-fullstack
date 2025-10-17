from flask import Blueprint, request, jsonify, Response, send_file
from datetime import datetime, timezone  # ← timezone 추가
import cv2
import numpy as np
import os
import threading

from models import db, StreamSession
from utils.buffer import CircularVideoBuffer, HLSSegmentManager
from config import Config

streaming_bp = Blueprint('streaming', __name__)

# 전역 변수
video_buffer = CircularVideoBuffer(duration=30, fps=30)  # 30초로 증가
hls_manager = HLSSegmentManager(Config.HLS_DIR, segment_duration=2)
current_stream_session = None
stream_lock = threading.Lock()

# 최신 프레임 저장 (MJPEG용)
latest_frame = None
frame_lock = threading.Lock()


@streaming_bp.route('/upload', methods=['POST'])
def upload_frame():
    """
    라즈베리파이로부터 프레임 수신

    Expected:
        - multipart/form-data
        - file: frame (JPEG)
        - device_id: 디바이스 ID
    """
    global latest_frame, current_stream_session

    try:
        # FIX #1: Enhanced logging - Log incoming request
        print(f"📥 Received frame upload request from device: {request.form.get('device_id', 'unknown')}")
        print(f"   Content-Type: {request.content_type}")
        print(f"   Content-Length: {request.content_length}")

        # 파일 확인
        if 'frame' not in request.files:
            print(f"❌ Frame validation failed: No 'frame' field in request")
            print(f"   Available fields: {list(request.files.keys())}")
            print(f"   Form data: {list(request.form.keys())}")
            return jsonify({'error': 'No frame provided'}), 400

        frame_file = request.files['frame']
        device_id = request.form.get('device_id', 'unknown')

        # 프레임 데이터 읽기
        frame_bytes = frame_file.read()
        frame_size = len(frame_bytes)

        # FIX #1: Log frame size and device_id
        print(f"✅ Frame received: {frame_size} bytes from {device_id}")

        # FIX #1: Frame validation
        if frame_size == 0:
            print(f"❌ Frame validation failed: Empty frame data from {device_id}")
            return jsonify({'error': 'Empty frame data'}), 400

        if frame_size > 10 * 1024 * 1024:  # 10MB limit
            print(f"⚠️ Frame validation warning: Large frame {frame_size} bytes from {device_id}")

        # 최신 프레임 저장 (MJPEG 스트리밍용)
        with frame_lock:
            latest_frame = frame_bytes

        # 순환 버퍼에 추가 - datetime.utcnow() → datetime.now(timezone.utc)로 수정
        video_buffer.add_frame(frame_bytes, datetime.now(timezone.utc))

        # FIX #5: Auto-create StreamSession if none exists
        with stream_lock:
            if current_stream_session is None or not current_stream_session.is_active:
                print(f"🔄 Auto-creating StreamSession for device: {device_id}")
                session = StreamSession(
                    device_id=device_id,
                    is_active=True
                )
                db.session.add(session)
                db.session.commit()
                current_stream_session = session
                print(f"✅ StreamSession auto-created: {session.id}")

            # 스트림 세션 업데이트
            if current_stream_session and current_stream_session.is_active:
                current_stream_session.total_frames += 1
                db.session.commit()

                # FIX #1: Log session statistics every 100 frames
                if current_stream_session.total_frames % 100 == 0:
                    print(f"📊 Session stats: {current_stream_session.total_frames} frames processed for {device_id}")

        return jsonify({
            'status': 'success',
            'buffer_status': video_buffer.get_status()
        }), 200

    except Exception as e:
        # FIX #1: Enhanced error logging with traceback
        print(f"❌ Frame upload failed: {e}")
        print(f"   Device: {request.form.get('device_id', 'unknown')}")
        print(f"   Content-Type: {request.content_type}")
        print(f"   Content-Length: {request.content_length}")

        # Print full traceback for debugging
        import traceback
        print("🔍 Full traceback:")
        traceback.print_exc()

        return jsonify({'error': str(e)}), 500


@streaming_bp.route('/mjpeg')
def mjpeg_stream():
    """
    MJPEG 스트리밍 엔드포인트 (실시간 영상)
    프론트엔드에서 <img src="/api/stream/mjpeg"> 형태로 사용

    CORS 헤더를 명시적으로 포함하여 네트워크 환경에서 스트리밍 지원
    """
    def generate():
        while True:
            with frame_lock:
                if latest_frame is None:
                    # 대기 프레임 (검은 화면)
                    dummy = np.zeros((480, 640, 3), dtype=np.uint8)
                    _, buffer = cv2.imencode('.jpg', dummy)
                    frame = buffer.tobytes()
                else:
                    frame = latest_frame

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            # FPS 제어 (30fps)
            import time
            time.sleep(1/30)

    # CORS 헤더 명시적 포함
    response = Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

    # 네트워크 스트리밍을 위한 추가 헤더
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response


@streaming_bp.route('/hls/playlist.m3u8')
def hls_playlist():
    """
    HLS 플레이리스트 (M3U8)
    """
    playlist = hls_manager.get_playlist()
    return Response(playlist, mimetype='application/vnd.apple.mpegurl')


@streaming_bp.route('/session/start', methods=['POST'])
def start_session():
    """스트리밍 세션 시작"""
    global current_stream_session
    
    data = request.get_json()
    device_id = data.get('device_id', 'pi-01')
    
    with stream_lock:
        # 기존 세션 종료
        if current_stream_session and current_stream_session.is_active:
            current_stream_session.is_active = False
            current_stream_session.ended_at = datetime.now(timezone.utc)  # ← 수정
        
        # 새 세션 생성
        session = StreamSession(
            device_id=device_id,
            is_active=True
        )
        
        db.session.add(session)
        db.session.commit()
        
        current_stream_session = session
        
        # 버퍼 초기화
        video_buffer.clear()
    
    return jsonify({
        'status': 'started',
        'session': session.to_dict()
    }), 200


@streaming_bp.route('/session/stop', methods=['POST'])
def stop_session():
    """스트리밍 세션 종료"""
    global current_stream_session
    
    with stream_lock:
        if current_stream_session and current_stream_session.is_active:
            current_stream_session.is_active = False
            current_stream_session.ended_at = datetime.now(timezone.utc)  # ← 수정
            db.session.commit()
            
            session_dict = current_stream_session.to_dict()
            current_stream_session = None
            
            return jsonify({
                'status': 'stopped',
                'session': session_dict
            }), 200
        else:
            return jsonify({'error': 'No active session'}), 400


@streaming_bp.route('/session/status')
def session_status():
    """현재 세션 상태"""
    with stream_lock:
        if current_stream_session and current_stream_session.is_active:
            return jsonify({
                'active': True,
                'session': current_stream_session.to_dict(),
                'buffer_status': video_buffer.get_status()
            }), 200
        else:
            return jsonify({
                'active': False,
                'buffer_status': video_buffer.get_status()
            }), 200


@streaming_bp.route('/buffer/status')
def buffer_status():
    """버퍼 상태 확인"""
    return jsonify(video_buffer.get_status()), 200


@streaming_bp.route('/frame/latest', methods=['GET'])
def get_latest_frame():
    """
    Get the latest single frame as JPEG image

    This endpoint returns the most recent frame received from the Raspberry Pi
    as a single JPEG image, suitable for snapshot display or periodic polling.

    Returns:
        - 200: JPEG image (image/jpeg)
        - 204: No frame available yet (no content)
        - 500: Internal server error

    CORS: Enabled for cross-origin requests
    CACHE: No-cache headers to ensure fresh frame delivery

    Usage:
        <img src="/api/stream/frame/latest" />
        OR
        fetch('/api/stream/frame/latest').then(r => r.blob())
    """
    try:
        with frame_lock:
            current_frame = latest_frame

        if current_frame is None:
            # Return 204 No Content if no frame available
            return Response(status=204)

        # Return the latest frame as JPEG
        response = Response(current_frame, mimetype='image/jpeg')

        # Add cache-control headers to prevent stale frame caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response
    except Exception as e:
        print(f"❌ Error serving latest frame: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to retrieve frame'}), 500


# 버퍼 접근 함수 (incidents.py에서 사용)
def get_video_buffer():
    """버퍼 인스턴스 반환"""
    return video_buffer


@streaming_bp.route('/endpoints', methods=['GET'])
def list_endpoints():
    """
    FIX #3: Endpoint discovery route
    Lists all streaming-related endpoints and their expected formats
    """
    endpoints = {
        'streaming_endpoints': [
            {
                'path': '/api/stream/upload',
                'method': 'POST',
                'description': 'Upload video frame from Raspberry Pi',
                'content_type': 'multipart/form-data',
                'parameters': {
                    'frame': 'file (JPEG image)',
                    'device_id': 'string (device identifier)'
                },
                'example_curl': 'curl -X POST http://localhost:5000/api/stream/upload -F "frame=@frame.jpg" -F "device_id=pi-01"'
            },
            {
                'path': '/api/stream/mjpeg',
                'method': 'GET',
                'description': 'Real-time MJPEG video stream',
                'content_type': 'multipart/x-mixed-replace',
                'parameters': None
            },
            {
                'path': '/api/stream/frame/latest',
                'method': 'GET',
                'description': 'Get latest single frame as JPEG snapshot',
                'content_type': 'image/jpeg',
                'parameters': None,
                'example_curl': 'curl -X GET http://localhost:5000/api/stream/frame/latest -o latest.jpg'
            },
            {
                'path': '/api/stream/hls/playlist.m3u8',
                'method': 'GET',
                'description': 'HLS playlist for video playback',
                'content_type': 'application/vnd.apple.mpegurl',
                'parameters': None
            },
            {
                'path': '/api/stream/session/start',
                'method': 'POST',
                'description': 'Start streaming session',
                'content_type': 'application/json',
                'parameters': {
                    'device_id': 'string (device identifier)'
                }
            },
            {
                'path': '/api/stream/session/stop',
                'method': 'POST',
                'description': 'Stop streaming session',
                'content_type': 'application/json',
                'parameters': None
            },
            {
                'path': '/api/stream/session/status',
                'method': 'GET',
                'description': 'Get current session status',
                'content_type': 'application/json',
                'parameters': None
            },
            {
                'path': '/api/stream/buffer/status',
                'method': 'GET',
                'description': 'Get video buffer status',
                'content_type': 'application/json',
                'parameters': None
            },
            {
                'path': '/api/stream/endpoints',
                'method': 'GET',
                'description': 'List all streaming endpoints (this endpoint)',
                'content_type': 'application/json',
                'parameters': None
            }
        ],
        'server_info': {
            'version': '1.0.0',
            'upload_endpoint_active': True,
            'expected_frame_format': 'JPEG',
            'max_frame_size': '10MB'
        }
    }
    return jsonify(endpoints), 200