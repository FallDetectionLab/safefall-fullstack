import os
from pathlib import Path
from dotenv import load_dotenv
import platform


def load_environment_config():
    """환경에 따라 적절한 .env 파일 로드"""
    base_dir = Path(__file__).resolve().parent
    
    # 환경 감지 (라즈베리파이 vs 로컬)
    is_raspberry_pi = platform.machine().startswith('arm') or os.path.exists('/opt/vc/bin/vcgencmd')
    env_name = os.getenv('SAFEFALL_ENV', 'pi' if is_raspberry_pi else 'local')
    
    # 환경별 .env 파일 로드
    env_files = [
        base_dir / f'.env.{env_name}',  # 환경별 설정 (우선)
        base_dir / '.env',              # 기본 설정
    ]
    
    for env_file in env_files:
        if env_file.exists():
            print(f"📝 Loading config from: {env_file}")
            load_dotenv(env_file, override=True)
            break
    else:
        print("⚠️ No environment config file found, using defaults")


# 환경 설정 로드
load_environment_config()


class Config:
    """Raspberry Pi client configuration"""

    # Base directory
    BASE_DIR = Path(__file__).resolve().parent

    # Backend server
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
    DEVICE_ID = os.getenv("DEVICE_ID", "pi-01")

    # YOLO model
    YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "models/yolo11n.pt")

    # Camera settings
    CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "1280"))
    CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "720"))
    CAMERA_FPS = int(os.getenv("CAMERA_FPS", "30"))

    # Detection settings
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    ASPECT_RATIO_THRESHOLD = float(os.getenv("ASPECT_RATIO_THRESHOLD", "1.5"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = BASE_DIR / "logs"

    @staticmethod
    def init():
        """Initialize directories"""
        Config.LOG_DIR.mkdir(exist_ok=True)
        (Config.BASE_DIR / "models").mkdir(exist_ok=True)
        print(f"✅ Initialization complete")
        print(f"   Backend: {Config.BACKEND_URL}")
        print(f"   Device: {Config.DEVICE_ID}")
