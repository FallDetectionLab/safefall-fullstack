import os
import sys
from datetime import timedelta
from pathlib import Path

class Config:
    """기본 설정"""
    # 기본 경로 (Windows 호환)
    BASE_DIR = Path(__file__).resolve().parent

    # Flask 기본 설정
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'

    # 데이터베이스 - instance 폴더에 생성
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI',
        f'sqlite:///{os.path.join(INSTANCE_DIR, "safefall.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database connection pool configuration (performance optimization)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,              # Maximum number of persistent connections
        'pool_recycle': 3600,         # Recycle connections after 1 hour
        'pool_pre_ping': True,        # Verify connections before using them
        'max_overflow': 20,           # Maximum overflow connections beyond pool_size
    }

    # JWT 설정
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 파일 저장 경로
    VIDEOS_DIR = os.path.join(BASE_DIR, 'videos')
    HLS_DIR = os.path.join(BASE_DIR, 'static', 'hls')
    
    # 스트리밍 설정
    STREAM_FPS = 30
    STREAM_RESOLUTION = (1280, 720)  # 720p
    HLS_SEGMENT_DURATION = 2  # 초
    BUFFER_DURATION = 30  # 사고 전후 저장할 시간 (초) - 15초 → 30초
    INCIDENT_VIDEO_DURATION = 30  # 총 저장 영상 길이 (초)
    
    # CORS 설정
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5174,http://safefall2.s3-website.ap-northeast-2.amazonaws.com').split(',')
    
    # 최대 업로드 크기
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

    @staticmethod
    def init_app(app):
        """앱 초기화 시 실행"""
        # 필요한 디렉토리 생성
        os.makedirs(Config.INSTANCE_DIR, exist_ok=True)  # instance 디렉토리 생성
        os.makedirs(Config.VIDEOS_DIR, exist_ok=True)
        os.makedirs(Config.HLS_DIR, exist_ok=True)


class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True


class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False

    # SECURITY: Enforce required secrets in production environment
    @classmethod
    def init_app(cls, app):
        """
        Initialize app and validate production configuration.

        SECURITY: Validates that critical secrets are set in production.
        This method is called during app initialization to enforce security requirements.
        """
        # Call parent init_app first to create directories
        super().init_app(app)

        # Check if critical secrets are properly set (not using default values)
        if app.config.get('SECRET_KEY') == 'dev-secret-key-change-in-production':
            raise RuntimeError(
                "SECURITY ERROR: SECRET_KEY must be set via environment variable in production. "
                "Never use the default development key in production!"
            )
        if app.config.get('JWT_SECRET_KEY') == 'jwt-secret-key-change-in-production':
            raise RuntimeError(
                "SECURITY ERROR: JWT_SECRET_KEY must be set via environment variable in production. "
                "Never use the default development key in production!"
            )
    

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}