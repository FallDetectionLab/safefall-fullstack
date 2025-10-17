"""
Videos API - 영상 관리 엔드포인트
로컬 버전의 비디오 관리 기능 통합
"""
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
import os

from models import db, Incident
from config import Config

videos_bp = Blueprint('videos', __name__)


def safe_path_join(base_dir, filename):
    """
    경로 순회 공격 방지
    """
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    if os.path.isabs(filename):
        raise ValueError("Absolute paths are not allowed")
    
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        raise ValueError("Path traversal attempts are not allowed")
    
    full_path = os.path.normpath(os.path.join(base_dir, filename))
    base_dir_abs = os.path.abspath(base_dir)
    full_path_abs = os.path.abspath(full_path)
    
    if not full_path_abs.startswith(base_dir_abs):
        raise ValueError("Path is outside the allowed directory")
    
    return full_path_abs


@videos_bp.route('/saved', methods=['GET'])
@jwt_required()
def get_saved_videos():
    """
    저장된 비디오 목록 조회
    
    Query Parameters:
        - trigger_type: 필터 (fall, manual 등)
        - limit: 조회 수 (기본: 50)
    """
    try:
        current_user_id = get_jwt_identity()
        trigger_type = request.args.get('trigger_type', None)
        limit = request.args.get('limit', 50, type=int)
        
        # 쿼리 빌드
        query = Incident.query.filter_by(user_id=current_user_id)
        
        if trigger_type:
            query = query.filter_by(incident_type=trigger_type)
        
        # 최신순 정렬
        incidents = query.order_by(Incident.detected_at.desc()).limit(limit).all()
        
        videos = []
        for incident in incidents:
            video_path = os.path.join(Config.VIDEOS_DIR, incident.video_path)
            
            # 파일 존재 확인
            if os.path.exists(video_path):
                stat = os.stat(video_path)
                
                video_data = {
                    'id': incident.id,
                    'title': f'SafeFall Video - {incident.video_path}',
                    'filename': incident.video_path,
                    'video_filename': incident.video_path,
                    'name': incident.video_path,
                    'path': f'/api/incidents/{incident.id}/video',
                    'url': f'http://localhost:5000/api/incidents/{incident.id}/video',
                    'thumbnail_url': f'/api/incidents/{incident.id}/thumbnail' if incident.thumbnail_path else None,
                    'size': stat.st_size,
                    'mtime': incident.detected_at.isoformat(),
                    'created_at': incident.detected_at.isoformat(),
                    'createdAt': incident.detected_at.isoformat(),
                    'confidence': incident.confidence or 0.95,
                    'isChecked': incident.is_checked,
                    'processed': incident.is_checked,
                    'trigger_type': incident.incident_type,
                    'device_id': incident.extra_data.get('device_id', 'unknown') if incident.extra_data else 'unknown',
                    'file_type': 'mp4'
                }
                videos.append(video_data)
        
        return jsonify({
            'success': True,
            'videos': videos,
            'count': len(videos),
            'method': 'Database'
        }), 200
        
    except Exception as e:
        print(f"❌ Get saved videos error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'videos': [],
            'count': 0
        }), 500


@videos_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent_videos():
    """최근 비디오 목록 (saved와 동일)"""
    return get_saved_videos()


@videos_bp.route('/<video_identifier>', methods=['GET'])
@jwt_required()
def get_video_by_identifier(video_identifier):
    """
    개별 비디오 정보 조회
    
    Parameters:
        - video_identifier: ID 또는 파일명
    """
    try:
        current_user_id = get_jwt_identity()
        
        # ID인지 파일명인지 판단
        if video_identifier.isdigit():
            # ID로 조회
            incident = Incident.query.filter_by(
                id=int(video_identifier),
                user_id=current_user_id
            ).first()
        else:
            # 파일명으로 조회
            from urllib.parse import unquote
            decoded_filename = unquote(video_identifier)
            
            incident = Incident.query.filter_by(
                video_path=decoded_filename,
                user_id=current_user_id
            ).first()
        
        if not incident:
            return jsonify({
                'success': False,
                'error': f'Video not found: {video_identifier}',
                'video': None
            }), 404
        
        # 파일 존재 확인
        video_path = os.path.join(Config.VIDEOS_DIR, incident.video_path)
        
        if not os.path.exists(video_path):
            return jsonify({
                'success': False,
                'error': f'Video file not found: {incident.video_path}',
                'video': None
            }), 404
        
        stat = os.stat(video_path)
        
        video_data = {
            'id': incident.id,
            'title': f'SafeFall Video - {incident.video_path}',
            'filename': incident.video_path,
            'video_filename': incident.video_path,
            'name': incident.video_path,
            'path': f'/api/incidents/{incident.id}/video',
            'url': f'http://localhost:5000/api/incidents/{incident.id}/video',
            'thumbnail_url': f'/api/incidents/{incident.id}/thumbnail' if incident.thumbnail_path else None,
            'size': stat.st_size,
            'mtime': incident.detected_at.isoformat(),
            'created_at': incident.detected_at.isoformat(),
            'createdAt': incident.detected_at.isoformat(),
            'confidence': incident.confidence or 0.95,
            'isChecked': incident.is_checked,
            'processed': incident.is_checked,
            'trigger_type': incident.incident_type,
            'device_id': incident.extra_data.get('device_id', 'unknown') if incident.extra_data else 'unknown'
        }
        
        return jsonify({
            'success': True,
            'video': video_data
        }), 200
        
    except Exception as e:
        print(f"❌ Get video by identifier error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'video': None
        }), 500


@videos_bp.route('/<int:video_id>/status', methods=['PUT'])
@jwt_required()
def update_video_status(video_id):
    """
    비디오 확인 상태 업데이트
    
    Body:
        - isChecked: boolean
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}
        is_checked = data.get('isChecked', False)
        
        # 사고 조회
        incident = Incident.query.filter_by(
            id=video_id,
            user_id=current_user_id
        ).first()
        
        if not incident:
            return jsonify({
                'success': False,
                'error': f'Video {video_id} not found'
            }), 404
        
        # 상태 업데이트
        incident.is_checked = is_checked
        if is_checked:
            incident.checked_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Video {video_id} status updated',
            'video': incident.to_dict()
        }), 200
        
    except Exception as e:
        print(f"❌ Update video status error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@videos_bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_videos():
    """
    디스크의 비디오 파일들을 데이터베이스와 동기화
    (파일시스템에는 있지만 DB에 없는 파일들을 등록)
    """
    try:
        current_user_id = get_jwt_identity()
        
        if not os.path.exists(Config.VIDEOS_DIR):
            return jsonify({
                'success': False,
                'error': 'Videos directory not found'
            }), 404
        
        print(f"🔍 동기화 시작: {Config.VIDEOS_DIR}")
        
        # 파일시스템의 비디오 파일 목록
        video_files = []
        for filename in os.listdir(Config.VIDEOS_DIR):
            if filename.lower().endswith(('.mp4', '.avi')):
                file_path = os.path.join(Config.VIDEOS_DIR, filename)
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    video_files.append({
                        'filename': filename,
                        'path': file_path,
                        'size': stat.st_size,
                        'mtime': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                    })
        
        print(f"📁 파일시스템 비디오: {len(video_files)}개")
        
        # DB의 기존 파일 목록
        db_incidents = Incident.query.filter_by(user_id=current_user_id).all()
        db_filenames = set(incident.video_path for incident in db_incidents)
        
        print(f"💾 DB 등록된 비디오: {len(db_filenames)}개")
        
        # 누락된 파일 찾기
        missing_videos = [v for v in video_files if v['filename'] not in db_filenames]
        
        print(f"🚨 누락된 영상 {len(missing_videos)}개 발견")
        
        # 누락된 영상 등록
        registered = []
        failed = []
        
        for video in missing_videos:
            try:
                # 새 사고 기록 생성
                incident = Incident(
                    user_id=current_user_id,
                    incident_type='fall',  # 기본 타입
                    detected_at=video['mtime'],
                    video_path=video['filename'],
                    duration=30.0,  # 기본값
                    confidence=0.90,
                    extra_data={
                        'device_id': 'sync',
                        'source': 'filesystem_sync'
                    }
                )
                
                db.session.add(incident)
                db.session.commit()
                
                registered.append({
                    'filename': video['filename'],
                    'incident_id': incident.id,
                    'timestamp': video['mtime'].isoformat()
                })
                
                print(f"  ✅ {video['filename']} -> ID:{incident.id}")
                
            except Exception as e:
                failed.append({
                    'filename': video['filename'],
                    'error': str(e)
                })
                print(f"  ❌ {video['filename']} 오류: {e}")
                db.session.rollback()
        
        return jsonify({
            'success': True,
            'total_videos': len(video_files),
            'db_videos_before': len(db_filenames),
            'missing_found': len(missing_videos),
            'registered': len(registered),
            'failed': len(failed),
            'registered_videos': registered,
            'failed_videos': failed,
            'message': f'{len(registered)}개 영상이 성공적으로 등록되었습니다'
        }), 200
        
    except Exception as e:
        print(f"❌ 영상 동기화 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
