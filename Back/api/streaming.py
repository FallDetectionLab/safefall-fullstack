from flask import Blueprint, request, jsonify, Response, send_file
from datetime import datetime, timezone, timedelta
import cv2
import numpy as np
import os
import threading
import time

from models import db, StreamSession
from utils.buffer import CircularVideoBuffer, HLSSegmentManager
from utils.detector import FallDetector
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

# YOLO11 Pose 낙상 감지기 초기화
fall_detector = None
detector_lock = threading.Lock()

def init_fall_detector():
    """Initialize fall detector (lazy loading)"""
    global fall_detector
    with detector_lock:
        if fall_detector is None:
            try:
                print("🚀 Initializing YOLO11 Fall Detector...")
                fall_detector = FallDetector()
                print("✅ Fall Detector initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Fall Detector: {e}")
                print("⚠️ Streaming will continue without fall detection")
                fall_detector = None
        return fall_detector


# 낙상 감지 쿨다운 관리
last_incident_time = {}
incident_cooldown = 10  # 10초 쿨다운


def create_incident_from_detection(app, device_id, fall_result):
    """
    낙상 감지 시 인시던트 생성 (백그라운드 스레드에서 실행)

    Args:
        app: Flask 애플리케이션 인스턴스
        device_id: 디바이스 ID
        fall_result: YOLO 낙상 감지 결과
    """
    global last_incident_time

    # Flask 애플리케이션 컨텍스트 설정 (DB 접근을 위해 필수)
    with app.app_context():
        try:
            # 쿨다운 체크 (너무 자주 인시던트 생성 방지)
            current_time = time.time()
            if device_id in last_incident_time:
                time_since_last = current_time - last_incident_time[device_id]
                if time_since_last < incident_cooldown:
                    print(f"⏳ 쿨다운 중... ({time_since_last:.1f}초 경과, {incident_cooldown}초 필요)")
                    return

            last_incident_time[device_id] = current_time

            # 인시던트 데이터 준비
            incident_data = {
                "device_id": device_id,
                "incident_type": "fall",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "confidence": float(fall_result.get('confidence', 0)),
                "user_id": "1",  # 기본 사용자 (필요시 환경변수로 설정)
                "extra_data": {
                    "aspect_ratio": float(fall_result.get('aspect_ratio', 0)),
                    "bbox": fall_result.get('bbox'),
                    "detection_source": "backend_yolo11"
                }
            }

            print(f"📝 인시던트 생성 중...")
            print(f"   Confidence: {incident_data['confidence']:.2f}")
            print(f"   Detected at: {incident_data['detected_at']}")

            # 데이터베이스에 인시던트 생성
            from models import db, Incident, User
            from utils.video import frames_to_video, create_thumbnail, get_video_info
            import time as time_module

            # 영상 저장 준비
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"incident_fall_{timestamp}.mp4"
            video_path = os.path.join(Config.VIDEOS_DIR, filename)

            # 버퍼에서 프레임 추출
            detected_at = datetime.fromisoformat(incident_data['detected_at'].replace('Z', '+00:00'))
            before_time = detected_at - timedelta(seconds=15)
            after_time = detected_at + timedelta(seconds=15)

            all_frames = video_buffer.get_all_frames()
            incident_frames = [
                frame for frame in all_frames
                if before_time <= frame["timestamp"] <= after_time
            ]

            if len(incident_frames) == 0:
                print("⚠️ 사고 시점 프레임 없음, 최신 프레임 사용")
                incident_frames = all_frames[-min(len(all_frames), 900):]  # 최대 30초 (30fps)

            print(f"📦 버퍼에서 {len(incident_frames)} 프레임 추출")

            # 영상 파일 저장
            success = frames_to_video(incident_frames, video_path, fps=None)

            if not success:
                print("❌ 영상 저장 실패")
                return

            time_module.sleep(0.2)  # 파일 시스템 동기화 대기

            # 썸네일 생성
            thumbnail_filename = f"thumb_{timestamp}.jpg"
            thumbnail_path = os.path.join(Config.VIDEOS_DIR, thumbnail_filename)
            thumbnail_success = create_thumbnail(video_path, thumbnail_path, time_offset=0)

            if not thumbnail_success:
                print("⚠️ 썸네일 생성 실패")
                thumbnail_filename = None

            # 비디오 정보
            video_info = get_video_info(video_path)

            # 사용자 확인
            user = User.query.filter_by(id=incident_data['user_id']).first()
            if not user:
                print(f"❌ 사용자를 찾을 수 없음: {incident_data['user_id']}")
                return

            # 인시던트 생성
            incident = Incident(
                user_id=incident_data['user_id'],
                incident_type='fall',
                detected_at=detected_at,
                video_path=filename,
                thumbnail_path=thumbnail_filename,
                duration=video_info['duration'] if video_info else 30.0,
                confidence=incident_data['confidence'],
                extra_data={
                    "device_id": device_id,
                    "frame_count": len(incident_frames),
                    "video_info": video_info,
                    "aspect_ratio": incident_data['extra_data']['aspect_ratio'],
                    "detection_source": "backend_yolo11"
                }
            )

            db.session.add(incident)
            db.session.commit()

            print(f"✅ 인시던트 생성 완료! ID: {incident.id}")
            print(f"   영상: {filename}")
            print(f"   지속시간: {incident.duration:.2f}초")

        except Exception as e:
            print(f"❌ 인시던트 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            try:
                db.session.rollback()
            except:
                pass


@streaming_bp.route('/upload', methods=['POST'])
def upload_frame():
    """
    라즈베리파이로부터 프레임 수신 및 YOLO 처리

    Expected:
        - multipart/form-data
        - file: frame (JPEG)
        - device_id: 디바이스 ID
    """
    global latest_frame, current_stream_session

    try:
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

        # Frame validation
        if frame_size == 0:
            print(f"❌ Frame validation failed: Empty frame data from {device_id}")
            return jsonify({'error': 'Empty frame data'}), 400

        if frame_size > 10 * 1024 * 1024:  # 10MB limit
            print(f"⚠️ Frame validation warning: Large frame {frame_size} bytes from {device_id}")

        # ⭐ YOLO 처리: 원본 프레임 → 주석된 프레임
        try:
            # Decode JPEG to numpy array
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                print(f"❌ Failed to decode frame from {device_id}")
                return jsonify({'error': 'Failed to decode frame'}), 400

            # Initialize detector if needed
            detector = init_fall_detector()

            if detector is not None:
                # YOLO 처리: 낙상 감지 + 바운딩 박스 그리기
                fall_result, annotated_frame = detector.detect(frame, draw_boxes=True)

                # 주석된 프레임을 JPEG로 인코딩
                _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                processed_frame_bytes = buffer.tobytes()

                # 낙상 감지 시 인시던트 생성
                if fall_result and fall_result.get('detected'):
                    confidence = fall_result.get('confidence', 0)
                    aspect_ratio = fall_result.get('aspect_ratio', 0)

                    print(f"🚨 Fall detected from {device_id}!")
                    print(f"   Confidence: {confidence:.2f}")
                    print(f"   Aspect Ratio: {aspect_ratio:.2f}")

                    # 인시던트 생성 (비동기로 처리)
                    # Flask 애플리케이션 인스턴스 전달
                    from flask import current_app
                    threading.Thread(
                        target=create_incident_from_detection,
                        args=(current_app._get_current_object(), device_id, fall_result),
                        daemon=True
                    ).start()
            else:
                # Detector 없으면 원본 프레임 사용
                processed_frame_bytes = frame_bytes

        except Exception as e:
            print(f"⚠️ YOLO processing error: {e}")
            # YOLO 처리 실패 시 원본 프레임 사용
            processed_frame_bytes = frame_bytes

        # 최신 프레임 저장 (MJPEG 스트리밍용) - 처리된 프레임 사용
        with frame_lock:
            latest_frame = processed_frame_bytes

        # 순환 버퍼에 추가 (처리된 프레임 사용)
        video_buffer.add_frame(processed_frame_bytes, datetime.now(timezone.utc))

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


@streaming_bp.route('/live', methods=['GET'])
def get_live_stream():
    """
    Get live stream information
    Returns the current stream URL and status
    """
    global current_stream_session, latest_frame
    
    try:
        with stream_lock:
            is_active = current_stream_session and current_stream_session.is_active
            has_frame = latest_frame is not None
        
        # MJPEG 스트림 URL 생성
        from flask import request
        base_url = request.url_root.rstrip('/')
        
        return jsonify({
            'success': True,
            'streamUrl': base_url,
            'status': 'online' if (is_active or has_frame) else 'offline',
            'quality': '720p',
            'type': 'mjpeg',
            'endpoints': {
                'mjpeg': f'{base_url}/api/stream/mjpeg',
                'latest_frame': f'{base_url}/api/stream/frame/latest',
                'hls_playlist': f'{base_url}/api/stream/hls/playlist.m3u8'
            },
            'active_session': is_active,
            'has_frames': has_frame
        }), 200
    except Exception as e:
        print(f"❌ Error getting live stream info: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'streamUrl': None,
            'status': 'error'
        }), 500


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