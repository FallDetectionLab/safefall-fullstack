from flask import Blueprint, request, jsonify, send_file, Response, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, timezone
import os
import threading
import time

from models import db, Incident, User
from utils.video import frames_to_video, create_thumbnail, get_video_info
from config import Config

incidents_bp = Blueprint('incidents', __name__)

# 사고 처리 락
incident_lock = threading.Lock()

# SECURITY: Input validation - allowed incident types
ALLOWED_INCIDENT_TYPES = {'fall', 'collapse', 'abnormal_behavior', 'emergency', 'unknown'}


def safe_path_join(base_dir, filename):
    """
    SECURITY: Prevent path traversal attacks by validating file paths.

    This function ensures that:
    1. The filename doesn't contain path traversal sequences (../)
    2. The final path is within the allowed base directory
    3. Absolute paths and dangerous characters are rejected

    Args:
        base_dir: The base directory (e.g., Config.VIDEOS_DIR)
        filename: The filename to join

    Returns:
        The safe, absolute path

    Raises:
        ValueError: If the path is invalid or potentially malicious
    """
    # Reject if filename is None or empty
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Reject absolute paths
    if os.path.isabs(filename):
        raise ValueError("Absolute paths are not allowed")

    # Reject path traversal attempts
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        raise ValueError("Path traversal attempts are not allowed")

    # Join and normalize the path
    full_path = os.path.normpath(os.path.join(base_dir, filename))

    # Ensure the final path is within the base directory
    base_dir_abs = os.path.abspath(base_dir)
    full_path_abs = os.path.abspath(full_path)

    if not full_path_abs.startswith(base_dir_abs):
        raise ValueError("Path is outside the allowed directory")

    return full_path_abs


@incidents_bp.route('/debug/<int:incident_id>', methods=['GET'])
def debug_incident(incident_id):
    """
    디버깅용 엔드포인트 - 사고 정보와 파일 경로 확인
    """
    try:
        # 사고 조회
        incident = Incident.query.filter_by(id=incident_id).first()
        
        if not incident:
            return jsonify({
                'error': 'Incident not found',
                'incident_id': incident_id
            }), 404
        
        # 경로 정보
        video_path = safe_path_join(Config.VIDEOS_DIR, incident.video_path)
        
        # 파일 존재 여부
        file_exists = os.path.exists(video_path)
        file_size = os.path.getsize(video_path) if file_exists else 0
        
        # videos 디렉토리 내용
        videos_dir_contents = []
        if os.path.exists(Config.VIDEOS_DIR):
            videos_dir_contents = os.listdir(Config.VIDEOS_DIR)
        
        debug_info = {
            'incident': {
                'id': incident.id,
                'video_path': incident.video_path,
                'detected_at': incident.detected_at.isoformat() if incident.detected_at else None,
                'user_id': incident.user_id
            },
            'paths': {
                'BASE_DIR': str(Config.BASE_DIR),
                'VIDEOS_DIR': Config.VIDEOS_DIR,
                'full_video_path': video_path,
                'file_exists': file_exists,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / 1024 / 1024, 2) if file_size > 0 else 0
            },
            'videos_directory': {
                'path': Config.VIDEOS_DIR,
                'exists': os.path.exists(Config.VIDEOS_DIR),
                'contents': videos_dir_contents,
                'file_count': len(videos_dir_contents)
            }
        }
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@incidents_bp.route('/report', methods=['POST'])
def report_incident():
    """
    사고 신호 수신 및 영상 저장

    NOTE: This endpoint is intentionally unauthenticated to allow IoT devices
    (Raspberry Pi, ESP32, etc.) to report incidents without JWT tokens.
    Consider implementing API key authentication if security is a concern.

    Expected JSON:
    {
        "device_id": "pi-01",
        "incident_type": "fall",
        "detected_at": "2025-01-10T12:34:56Z",
        "confidence": 0.95,
        "user_id": 1  (optional)
    }
    """
    try:
        data = request.get_json()

        # 필수 필드 확인
        if not data.get('incident_type'):
            return jsonify({'error': 'incident_type required'}), 400

        incident_type = data['incident_type']

        # SECURITY: Input validation - validate incident_type
        if incident_type not in ALLOWED_INCIDENT_TYPES:
            return jsonify({
                'error': 'Invalid incident_type',
                'message': f'Allowed types: {", ".join(ALLOWED_INCIDENT_TYPES)}'
            }), 400

        detected_at_str = data.get('detected_at')
        confidence = data.get('confidence', 0.0)
        # CRITICAL FIX: User.id is String(50), not Integer
        # Use 'admin' as default user_id (string)
        user_id = data.get('user_id', 'admin')

        # 시간 파싱
        if detected_at_str:
            detected_at = datetime.fromisoformat(detected_at_str.replace('Z', '+00:00'))
        else:
            detected_at = datetime.now(timezone.utc)

        print(f"🚨 사고 신호 수신: {incident_type} at {detected_at}")

        # PERFORMANCE & SECURITY: Use try-except-finally to ensure proper cleanup
        with incident_lock:
            video_path = None
            thumbnail_path = None

            try:
                # 버퍼에서 영상 추출
                from api.streaming import get_video_buffer
                video_buffer = get_video_buffer()

                # 사고 전후 15초씩 추출
                before_time = detected_at - timedelta(seconds=15)
                after_time = detected_at + timedelta(seconds=15)

                all_frames = video_buffer.get_all_frames()

                # 사고 전후 30초 구간의 프레임만 필터링
                incident_frames = [
                    frame for frame in all_frames
                    if before_time <= frame['timestamp'] <= after_time
                ]

                # 프레임이 부족한 경우 가능한 만큼 사용
                if len(incident_frames) == 0:
                    print("⚠️ 사고 시점 프레임 없음, 최신 프레임 사용")
                    # 버퍼의 모든 프레임 사용
                    incident_frames = all_frames

                print(f"📦 버퍼에서 {len(incident_frames)} 프레임 추출")
                if incident_frames:
                    time_span = (incident_frames[-1]['timestamp'] - incident_frames[0]['timestamp']).total_seconds()
                    print(f"   시간 범위: {time_span:.2f}초")

                # 영상 파일 저장
                timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                filename = f"incident_{incident_type}_{timestamp}.mp4"
                video_path = os.path.join(Config.VIDEOS_DIR, filename)

                # 프레임을 비디오로 변환 (FPS 자동 계산)
                success = frames_to_video(incident_frames, video_path, fps=None)

                if not success:
                    return jsonify({'error': 'Failed to save video'}), 500

                # 비디오 저장 후 잠시 대기 (파일 시스템 동기화)
                time.sleep(0.2)

                # 썸네일 생성
                thumbnail_filename = f"thumb_{timestamp}.jpg"
                thumbnail_path = os.path.join(Config.VIDEOS_DIR, thumbnail_filename)

                # 썸네일 생성 (중간 프레임 사용)
                thumbnail_success = create_thumbnail(video_path, thumbnail_path, time_offset=0)

                if not thumbnail_success:
                    print("⚠️ 썸네일 생성 실패, None으로 저장")
                    thumbnail_filename = None
                    thumbnail_path = None  # Reset path if creation failed

                # 비디오 정보
                video_info = get_video_info(video_path)

                # CRITICAL: Verify user exists before creating incident
                from models import User
                user = User.query.filter_by(id=user_id).first()
                if not user:
                    raise ValueError(
                        f"User with id='{user_id}' does not exist. "
                        f"Run 'python init_default_user.py' to create default user."
                    )

                # 데이터베이스에 저장
                incident = Incident(
                    user_id=user_id,
                    incident_type=incident_type,
                    detected_at=detected_at,
                    video_path=filename,
                    thumbnail_path=thumbnail_filename,
                    duration=video_info['duration'] if video_info else 30.0,
                    confidence=confidence,
                    extra_data={
                        'device_id': data.get('device_id', 'unknown'),
                        'frame_count': len(incident_frames),
                        'video_info': video_info
                    }
                )

                db.session.add(incident)
                db.session.commit()

                print(f"✅ 사고 영상 저장 완료: {filename}")
                if thumbnail_filename:
                    print(f"✅ 썸네일 저장 완료: {thumbnail_filename}")

                return jsonify({
                    'status': 'success',
                    'message': 'Incident recorded',
                    'incident': incident.to_dict()
                }), 201

            except Exception as e:
                # SECURITY: Clean up created files before rollback to prevent orphaned files
                if video_path and os.path.exists(video_path):
                    try:
                        os.remove(video_path)
                        print(f"🗑️ Cleaned up video file: {video_path}")
                    except Exception as cleanup_error:
                        print(f"⚠️ Failed to cleanup video file: {cleanup_error}")

                if thumbnail_path and os.path.exists(thumbnail_path):
                    try:
                        os.remove(thumbnail_path)
                        print(f"🗑️ Cleaned up thumbnail file: {thumbnail_path}")
                    except Exception as cleanup_error:
                        print(f"⚠️ Failed to cleanup thumbnail file: {cleanup_error}")

                # SECURITY: Rollback database transaction on failure
                db.session.rollback()
                raise e

    except Exception as e:
        print(f"❌ 사고 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@incidents_bp.route('/list', methods=['GET'])
@jwt_required()
def list_incidents():
    """사고 목록 조회"""
    current_user_id = get_jwt_identity()
    
    # 쿼리 파라미터
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    incident_type = request.args.get('type')
    is_checked = request.args.get('is_checked')
    
    # 쿼리 빌드
    query = Incident.query.filter_by(user_id=current_user_id)
    
    if incident_type:
        query = query.filter_by(incident_type=incident_type)
    
    if is_checked is not None:
        is_checked_bool = is_checked.lower() == 'true'
        query = query.filter_by(is_checked=is_checked_bool)
    
    # 최신순 정렬
    query = query.order_by(Incident.detected_at.desc())
    
    # 페이지네이션
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'videos': [incident.to_dict() for incident in pagination.items],
        'incidents': [incident.to_dict() for incident in pagination.items],
        'count': pagination.total,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@incidents_bp.route('/<int:incident_id>', methods=['GET'])
@jwt_required()
def get_incident(incident_id):
    """사고 상세 조회"""
    current_user_id = get_jwt_identity()
    
    incident = Incident.query.filter_by(
        id=incident_id,
        user_id=current_user_id
    ).first()
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    return jsonify(incident.to_dict()), 200


@incidents_bp.route('/<int:incident_id>/video', methods=['GET'])
def get_video(incident_id):
    """
    사고 영상 스트리밍 - 단순화된 Range 요청 지원
    
    JWT 인증 제거하여 HTML video 태그에서 직접 사용 가능
    """
    try:
        print(f"\n{'='*80}")
        print(f"🎬 [VIDEO REQUEST] Incident ID: {incident_id}")
        print(f"   Method: {request.method}")
        print(f"   URL: {request.url}")
        print(f"   Remote Addr: {request.remote_addr}")
        
        # 헤더 출력
        print(f"📋 [VIDEO REQUEST] Headers:")
        for key, value in request.headers:
            print(f"   {key}: {value}")
        
        # 사고 조회
        incident = Incident.query.filter_by(id=incident_id).first()
        
        if not incident:
            print(f"❌ [VIDEO REQUEST] Incident {incident_id} not found in database")
            return jsonify({'error': 'Incident not found', 'incident_id': incident_id}), 404
        
        print(f"✅ [VIDEO REQUEST] Found incident:")
        print(f"   video_path (DB): {incident.video_path}")
        print(f"   user_id: {incident.user_id}")
        print(f"   detected_at: {incident.detected_at}")
        
        # 경로 정보 출력
        print(f"📁 [VIDEO REQUEST] Path info:")
        print(f"   Config.VIDEOS_DIR: {Config.VIDEOS_DIR}")
        
        # 파일 경로 검증
        try:
            video_path = safe_path_join(Config.VIDEOS_DIR, incident.video_path)
            print(f"   Full path: {video_path}")
        except ValueError as e:
            print(f"❌ [VIDEO REQUEST] Invalid path: {e}")
            return jsonify({'error': 'Invalid file path', 'message': str(e)}), 400
        
        # 파일 존재 확인
        if not os.path.exists(video_path):
            print(f"❌ [VIDEO REQUEST] File not found!")
            print(f"   Expected path: {video_path}")
            print(f"   Directory exists: {os.path.exists(Config.VIDEOS_DIR)}")
            if os.path.exists(Config.VIDEOS_DIR):
                print(f"   Files in directory:")
                for f in os.listdir(Config.VIDEOS_DIR):
                    print(f"     - {f}")
            return jsonify({
                'error': 'Video file not found', 
                'expected_path': video_path,
                'filename': incident.video_path
            }), 404
        
        # 파일 정보 출력
        file_size = os.path.getsize(video_path)
        print(f"✅ [VIDEO REQUEST] File found!")
        print(f"   Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
        
        # Range 헤더 확인
        range_header = request.headers.get('Range')
        print(f"📊 [VIDEO REQUEST] Range header: {range_header}")
        
        # Range 요청이 없으면 전체 파일 전송
        if not range_header:
            print(f"✅ [VIDEO REQUEST] Sending full file (no Range header)")
            try:
                response = send_file(
                    video_path,
                    mimetype='video/mp4',
                    as_attachment=False
                )
                # 중요: Accept-Ranges 헤더 추가
                response.headers['Accept-Ranges'] = 'bytes'
                response.headers['Content-Length'] = str(file_size)
                response.headers['Cache-Control'] = 'no-cache'
                
                print(f"✅ [VIDEO REQUEST] Full file response prepared")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                print(f"   Content-Length: {response.headers.get('Content-Length')}")
                print(f"   Accept-Ranges: {response.headers.get('Accept-Ranges')}")
                print(f"{'='*80}\n")
                return response
            except Exception as e:
                print(f"❌ [VIDEO REQUEST] send_file error: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'Failed to send file: {str(e)}'}), 500
        
        # Range 요청 파싱
        try:
            # "bytes=0-1023" 또는 "bytes=1024-" 형식
            range_value = range_header.replace('bytes=', '').strip()
            parts = range_value.split('-')
            
            byte_start = int(parts[0]) if parts[0] else 0
            byte_end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
            
            # 범위 검증
            if byte_start < 0 or byte_end >= file_size or byte_start > byte_end:
                print(f"❌ [VIDEO REQUEST] Invalid range: {byte_start}-{byte_end} (file size: {file_size})")
                return Response(
                    'Requested Range Not Satisfiable',
                    status=416,
                    headers={'Content-Range': f'bytes */{file_size}'}
                )
            
            print(f"✅ [VIDEO REQUEST] Valid range: {byte_start}-{byte_end}")
            
        except (ValueError, IndexError) as e:
            print(f"⚠️ [VIDEO REQUEST] Invalid Range format: {range_header}, error: {e}")
            # Range 형식이 잘못되면 전체 파일 전송
            response = send_file(
                video_path,
                mimetype='video/mp4',
                as_attachment=False
            )
            response.headers['Accept-Ranges'] = 'bytes'
            print(f"{'='*80}\n")
            return response
        
        # 부분 콘텐츠 읽기
        length = byte_end - byte_start + 1
        
        try:
            with open(video_path, 'rb') as f:
                f.seek(byte_start)
                data = f.read(length)
            
            print(f"✅ [VIDEO REQUEST] Read {len(data):,} bytes from file")
            
            # 206 Partial Content 응답
            response = Response(
                data,
                status=206,
                mimetype='video/mp4',
                direct_passthrough=True
            )
            
            # 필수 헤더 설정
            response.headers['Content-Range'] = f'bytes {byte_start}-{byte_end}/{file_size}'
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Content-Length'] = str(length)
            response.headers['Cache-Control'] = 'no-cache'
            
            print(f"✅ [VIDEO REQUEST] Sending 206 Partial Content")
            print(f"   Content-Range: bytes {byte_start}-{byte_end}/{file_size}")
            print(f"   Content-Length: {length}")
            print(f"{'='*80}\n")
            
            return response
            
        except Exception as e:
            print(f"❌ [VIDEO REQUEST] Error reading file: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
            return jsonify({'error': f'Failed to read file: {str(e)}'}), 500
    
    except Exception as e:
        print(f"❌ [VIDEO REQUEST] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}\n")
        return jsonify({'error': str(e)}), 500


@incidents_bp.route('/<int:incident_id>/thumbnail', methods=['GET'])
# @jwt_required()  # ✅ JWT 인증 제거
def get_thumbnail(incident_id):
    """
    사고 썸네일
    """
    # current_user_id = get_jwt_identity()  # ✅ 주석 처리

    # Verify user owns this incident
    incident = Incident.query.filter_by(
        id=incident_id
        # user_id=current_user_id  # ✅ 사용자 검증 제거
    ).first()

    if not incident or not incident.thumbnail_path:
        return jsonify({'error': 'Thumbnail not found'}), 404

    # SECURITY: Use safe_path_join to prevent path traversal attacks
    try:
        thumbnail_path = safe_path_join(Config.VIDEOS_DIR, incident.thumbnail_path)
    except ValueError as e:
        return jsonify({'error': 'Invalid file path', 'message': str(e)}), 400

    if not os.path.exists(thumbnail_path):
        return jsonify({'error': 'Thumbnail file not found'}), 404

    return send_file(thumbnail_path, mimetype='image/jpeg')


@incidents_bp.route('/<int:incident_id>/check', methods=['PATCH'])
@jwt_required()
def check_incident(incident_id):
    """사고 확인 처리"""
    current_user_id = get_jwt_identity()

    # 🔍 DEBUG: Log the request
    print(f"🔍 [CHECK INCIDENT] Received request:")
    print(f"   Incident ID: {incident_id}")
    print(f"   Current user ID: {current_user_id}")

    # First, check if incident exists at all
    incident = Incident.query.filter_by(id=incident_id).first()

    if not incident:
        print(f"❌ [CHECK INCIDENT] Incident {incident_id} does not exist in database")
        return jsonify({'error': 'Incident not found'}), 404

    print(f"✅ [CHECK INCIDENT] Incident found: user_id={incident.user_id}, is_checked={incident.is_checked}")

    # Check if user owns this incident
    if incident.user_id != current_user_id:
        print(f"⚠️ [CHECK INCIDENT] User ID mismatch: incident.user_id={incident.user_id} != current_user_id={current_user_id}")
        return jsonify({'error': 'Incident not found'}), 404

    incident.is_checked = True
    incident.checked_at = datetime.now(timezone.utc)
    db.session.commit()

    print(f"✅ [CHECK INCIDENT] Incident {incident_id} marked as checked successfully")

    return jsonify({
        'status': 'success',
        'incident': incident.to_dict()
    }), 200


@incidents_bp.route('/<int:incident_id>', methods=['DELETE'])
@jwt_required()
def delete_incident(incident_id):
    """사고 삭제"""
    current_user_id = get_jwt_identity()

    incident = Incident.query.filter_by(
        id=incident_id,
        user_id=current_user_id
    ).first()

    if not incident:
        return jsonify({'error': 'Incident not found'}), 404

    # SECURITY: Use safe_path_join to prevent path traversal attacks on file deletion
    # Delete video file
    try:
        video_path = safe_path_join(Config.VIDEOS_DIR, incident.video_path)
        if os.path.exists(video_path):
            os.remove(video_path)
    except ValueError as e:
        # Log the error but continue with database deletion
        print(f"⚠️ Invalid video path during deletion: {e}")
    except Exception as e:
        # Log file deletion failure but continue
        print(f"⚠️ Failed to delete video file: {e}")

    # Delete thumbnail file
    if incident.thumbnail_path:
        try:
            thumbnail_path = safe_path_join(Config.VIDEOS_DIR, incident.thumbnail_path)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except ValueError as e:
            # Log the error but continue with database deletion
            print(f"⚠️ Invalid thumbnail path during deletion: {e}")
        except Exception as e:
            # Log file deletion failure but continue
            print(f"⚠️ Failed to delete thumbnail file: {e}")

    # DB 삭제 - Always proceed with database deletion even if files fail
    try:
        db.session.delete(incident)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete incident from database', 'message': str(e)}), 500

    return jsonify({'status': 'success', 'message': 'Incident deleted'}), 200


@incidents_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    통계

    PERFORMANCE: Optimized to use a single aggregated query instead of multiple
    separate queries (N+1 problem fix). This reduces database load significantly.
    """
    from sqlalchemy import func, case

    current_user_id = get_jwt_identity()

    # PERFORMANCE: Single optimized query with aggregations
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Aggregate all statistics in one query
    stats_query = db.session.query(
        func.count(Incident.id).label('total'),
        func.sum(case((Incident.is_checked == True, 1), else_=0)).label('checked'),
        func.sum(case((Incident.detected_at >= today_start, 1), else_=0)).label('today')
    ).filter(Incident.user_id == current_user_id).first()

    total = stats_query.total or 0
    checked = stats_query.checked or 0
    today = stats_query.today or 0
    unchecked = total - checked

    # 유형별 통계 (separate query but necessary for grouping)
    type_stats = db.session.query(
        Incident.incident_type,
        func.count(Incident.id)
    ).filter_by(user_id=current_user_id).group_by(Incident.incident_type).all()

    return jsonify({
        'total': total,
        'checked': checked,
        'unchecked': unchecked,
        'today': today,
        'by_type': {t: c for t, c in type_stats}
    }), 200
