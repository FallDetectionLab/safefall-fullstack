from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """사용자 모델

    NOTE: 스키마 변경 사항 (2025-10-08)
    - id 필드: Integer -> String (사용자 아이디로 사용)
    - username 필드: 사용자 닉네임으로 용도 변경
    - email 필드: nullable=True로 변경 (선택 사항)

    WARNING: 기존 데이터베이스와 호환되지 않습니다.
    마이그레이션 가이드는 README_MIGRATION.md를 참조하세요.
    """
    __tablename__ = 'users'

    # 사용자 아이디 (로그인용, Primary Key)
    id = db.Column(db.String(50), primary_key=True)

    # 사용자 닉네임 (표시용)
    username = db.Column(db.String(50), nullable=False, index=True)

    # 이메일 (선택 사항)
    email = db.Column(db.String(120), unique=True, nullable=True)

    # 비밀번호 해시
    password_hash = db.Column(db.String(255), nullable=False)

    # 메타데이터
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

    # 관계
    incidents = db.relationship('Incident', backref='user', lazy='dynamic')

    def set_password(self, password):
        """비밀번호 해시 설정"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """비밀번호 확인"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


class Incident(db.Model):
    """사고 기록 모델"""
    __tablename__ = 'incidents'

    # PERFORMANCE: Added composite indices for common query patterns
    __table_args__ = (
        # Index for filtering by user and incident type (used in /list endpoint)
        db.Index('idx_user_incident_type', 'user_id', 'incident_type'),
        # Index for filtering by user and checked status (used in /list endpoint)
        db.Index('idx_user_checked', 'user_id', 'is_checked'),
        # Index for filtering by user and time (used in /stats endpoint for "today" count)
        db.Index('idx_user_detected_at', 'user_id', 'detected_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)

    # 사고 정보
    incident_type = db.Column(db.String(50), nullable=False)  # fall, collapse, etc.
    detected_at = db.Column(db.DateTime, nullable=False)  # Composite index exists: idx_user_detected_at

    # 영상 정보
    video_path = db.Column(db.String(255), nullable=False)
    thumbnail_path = db.Column(db.String(255))
    duration = db.Column(db.Float, default=30.0)  # 초

    # 영상 및 썸네일 BLOB 저장 (선택적)
    video_blob = db.Column(db.LargeBinary)  # 영상 파일 바이너리
    thumbnail_blob = db.Column(db.LargeBinary)  # 썸네일 파일 바이너리

    # 상태
    is_checked = db.Column(db.Boolean, default=False)  # 확인 여부
    checked_at = db.Column(db.DateTime)

    # 메타데이터
    confidence = db.Column(db.Float)  # YOLO 신뢰도
    extra_data = db.Column(db.JSON)  # 추가 정보 (JSON)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'incident_type': self.incident_type,
            'detected_at': self.detected_at.isoformat(),
            'video_path': self.video_path,
            'thumbnail_path': self.thumbnail_path,
            'duration': self.duration,
            'is_checked': self.is_checked,
            'checked_at': self.checked_at.isoformat() if self.checked_at else None,
            'confidence': self.confidence,
            'extra_data': self.extra_data,  # metadata → extra_data로 수정
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            # Field aliases for frontend compatibility
            'filename': self.video_path,
            'createdAt': self.detected_at.isoformat(),
            'isChecked': self.is_checked,
            'processed': self.is_checked,
            'type': self.incident_type
        }


class StreamSession(db.Model):
    """스트리밍 세션 모델"""
    __tablename__ = 'stream_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(100), nullable=False, index=True)
    
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = db.Column(db.DateTime)
    
    is_active = db.Column(db.Boolean, default=True)
    
    # 통계
    total_frames = db.Column(db.Integer, default=0)
    incidents_detected = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'is_active': self.is_active,
            'total_frames': self.total_frames,
            'incidents_detected': self.incidents_detected
        }