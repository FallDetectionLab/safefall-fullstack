import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    """Raspberry Pi client configuration"""
    
    # Base directory
    BASE_DIR = Path(__file__).resolve().parent
    
    # Backend server
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')
    DEVICE_ID = os.getenv('DEVICE_ID', 'pi-01')
    
    # YOLO model
    YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', 'models/yolo11n.pt')
    
    # Camera settings
    CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', '1280'))
    CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', '720'))
    CAMERA_FPS = int(os.getenv('CAMERA_FPS', '30'))
    
    # Detection settings
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
    ASPECT_RATIO_THRESHOLD = float(os.getenv('ASPECT_RATIO_THRESHOLD', '1.5'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = BASE_DIR / 'logs'
    
    @staticmethod
    def init():
        """Initialize directories"""
        Config.LOG_DIR.mkdir(exist_ok=True)
        (Config.BASE_DIR / 'models').mkdir(exist_ok=True)
        print(f"✅ Initialization complete")
        print(f"   Backend: {Config.BACKEND_URL}")
        print(f"   Device: {Config.DEVICE_ID}")

