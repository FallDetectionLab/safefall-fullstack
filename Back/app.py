import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# 현재 디렉토리를 Python 경로에 추가
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import config
from models import db

def create_app(config_name='development'):
    """Flask 앱 팩토리"""
    app = Flask(__name__)
    
    # 설정 로드
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 확장 초기화
    db.init_app(app)

    # CORS 설정: 스트리밍 엔드포인트를 위한 추가 설정
    cors_config = {
        'resources': {r"/api/*": {"origins": "*"}},  # 모든 /api/* 엔드포인트에 CORS 적용
        'origins': app.config['CORS_ORIGINS'],
        'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],  # PATCH 메서드 추가
        'allow_headers': ['Content-Type', 'Authorization'],
        'expose_headers': ['Content-Type', 'Cache-Control', 'Pragma', 'Expires'],
        'supports_credentials': True,
        'max_age': 3600
    }
    CORS(app, **cors_config)

    jwt = JWTManager(app)

    # FIX #2: Request logging middleware
    @app.before_request
    def log_streaming_requests():
        """
        Log all incoming requests to streaming endpoints
        This helps diagnose if frames are arriving from Raspberry Pi devices
        """
        if request.path.startswith('/api/stream'):
            print(f"🌐 Incoming request: {request.method} {request.path}")
            print(f"   Remote addr: {request.remote_addr}")
            print(f"   Content-Type: {request.content_type}")
            print(f"   Content-Length: {request.content_length}")
            if request.args:
                print(f"   Query params: {dict(request.args)}")

    # 데이터베이스 초기화
    with app.app_context():
        db.create_all()
        print("✅ 데이터베이스 초기화 완료")
    
    # 블루프린트 등록
    register_blueprints(app)

    # 에러 핸들러
    register_error_handlers(app)

    # Frame endpoint (serves latest frame directly)
    @app.route('/api/frame/latest')
    def frame_latest():
        """
        Get the latest single frame as JPEG image

        This endpoint provides backward compatibility for frontend code expecting
        the /api/frame/latest endpoint. It directly accesses the latest_frame
        from the streaming module.

        Returns:
            - 200: JPEG image (image/jpeg)
            - 204: No frame available yet (no content)
            - 500: Internal server error

        BEST PRACTICE: This is a convenience endpoint that wraps the streaming
        module's functionality. The canonical endpoint is /api/stream/frame/latest
        """
        try:
            from flask import Response
            from api.streaming import latest_frame, frame_lock

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

    # 헬스체크
    @app.route('/health')
    def health():
        """
        Health check endpoint with comprehensive system checks.

        BEST PRACTICE: Returns 503 if critical services are unavailable,
        allowing load balancers to route traffic appropriately.
        """
        health_status = {
            'status': 'healthy',
            'message': 'SafeFall Backend Running',
            'version': '1.0.0',
            'checks': {}
        }
        status_code = 200

        # Check database connectivity
        try:
            # Simple query to test database connection
            db.session.execute(db.text('SELECT 1'))
            health_status['checks']['database'] = 'connected'
        except Exception as e:
            health_status['checks']['database'] = f'error: {str(e)}'
            health_status['status'] = 'unhealthy'
            status_code = 503

        # FIX #4: Check streaming blueprint registration
        try:
            streaming_bp_registered = 'streaming' in [bp.name for bp in app.blueprints.values()]
            if streaming_bp_registered:
                health_status['checks']['streaming_blueprint'] = 'registered'
            else:
                health_status['checks']['streaming_blueprint'] = 'not registered'
                health_status['status'] = 'degraded'
                if status_code == 200:
                    status_code = 503
        except Exception as e:
            health_status['checks']['streaming_blueprint'] = f'error: {str(e)}'
            health_status['status'] = 'unhealthy'
            status_code = 503

        # FIX #4: Check video_buffer and active_session status
        try:
            # Import streaming module to check buffer status
            from api.streaming import video_buffer, current_stream_session
            buffer_status = video_buffer.get_status()
            health_status['checks']['video_buffer'] = {
                'frame_count': buffer_status.get('frame_count', 0),
                'capacity': buffer_status.get('capacity', 0),
                'status': 'active'
            }

            # Check active session
            if current_stream_session and current_stream_session.is_active:
                health_status['checks']['active_session'] = {
                    'session_id': current_stream_session.id,
                    'device_id': current_stream_session.device_id,
                    'total_frames': current_stream_session.total_frames,
                    'status': 'active'
                }
            else:
                health_status['checks']['active_session'] = 'no active session'
        except Exception as e:
            health_status['checks']['streaming_status'] = f'error: {str(e)}'
            # This is not critical, so don't change overall status

        # Check video directory existence and writability
        try:
            videos_dir = app.config.get('VIDEOS_DIR')
            if videos_dir and os.path.exists(videos_dir):
                # Test writability
                test_file = os.path.join(videos_dir, '.health_check')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    health_status['checks']['videos_directory'] = 'accessible'
                except Exception as write_error:
                    health_status['checks']['videos_directory'] = f'not writable: {str(write_error)}'
                    health_status['status'] = 'degraded'
                    if status_code == 200:
                        status_code = 503
                finally:
                    # SECURITY: Always remove test file in finally block to ensure cleanup
                    try:
                        if os.path.exists(test_file):
                            os.remove(test_file)
                    except Exception:
                        pass  # Ignore cleanup errors
            else:
                health_status['checks']['videos_directory'] = 'not found'
                health_status['status'] = 'degraded'
                if status_code == 200:
                    status_code = 503
        except Exception as e:
            health_status['checks']['videos_directory'] = f'error: {str(e)}'
            health_status['status'] = 'unhealthy'
            status_code = 503

        return jsonify(health_status), status_code
    
    return app


def register_blueprints(app):
    """블루프린트 등록"""
    try:
        # 절대 경로로 import 시도
        import importlib.util
        import sys
        
        # auth.py 로드
        auth_path = os.path.join(BASE_DIR, 'api', 'auth.py')
        spec = importlib.util.spec_from_file_location("api.auth", auth_path)
        auth_module = importlib.util.module_from_spec(spec)
        sys.modules['api.auth'] = auth_module
        spec.loader.exec_module(auth_module)
        
        # streaming.py 로드
        streaming_path = os.path.join(BASE_DIR, 'api', 'streaming.py')
        spec = importlib.util.spec_from_file_location("api.streaming", streaming_path)
        streaming_module = importlib.util.module_from_spec(spec)
        sys.modules['api.streaming'] = streaming_module
        spec.loader.exec_module(streaming_module)
        
        # incidents.py 로드
        incidents_path = os.path.join(BASE_DIR, 'api', 'incidents.py')
        spec = importlib.util.spec_from_file_location("api.incidents", incidents_path)
        incidents_module = importlib.util.module_from_spec(spec)
        sys.modules['api.incidents'] = incidents_module
        spec.loader.exec_module(incidents_module)

        # notifications.py 로드
        notifications_path = os.path.join(BASE_DIR, 'api', 'notifications.py')
        spec = importlib.util.spec_from_file_location("api.notifications", notifications_path)
        notifications_module = importlib.util.module_from_spec(spec)
        sys.modules['api.notifications'] = notifications_module
        spec.loader.exec_module(notifications_module)
        
        # dashboard.py 로드
        dashboard_path = os.path.join(BASE_DIR, 'api', 'dashboard.py')
        spec = importlib.util.spec_from_file_location("api.dashboard", dashboard_path)
        dashboard_module = importlib.util.module_from_spec(spec)
        sys.modules['api.dashboard'] = dashboard_module
        spec.loader.exec_module(dashboard_module)
        
        # videos.py 로드
        videos_path = os.path.join(BASE_DIR, 'api', 'videos.py')
        spec = importlib.util.spec_from_file_location("api.videos", videos_path)
        videos_module = importlib.util.module_from_spec(spec)
        sys.modules['api.videos'] = videos_module
        spec.loader.exec_module(videos_module)

        # 블루프린트 등록
        app.register_blueprint(auth_module.auth_bp, url_prefix='/api/auth')
        app.register_blueprint(streaming_module.streaming_bp, url_prefix='/api/stream')
        app.register_blueprint(incidents_module.incidents_bp, url_prefix='/api/incidents')
        app.register_blueprint(notifications_module.notifications_bp, url_prefix='/api/v1/notifications')
        app.register_blueprint(dashboard_module.dashboard_bp, url_prefix='/api/dashboard')
        app.register_blueprint(videos_module.videos_bp, url_prefix='/api/videos')

        print("✅ API 블루프린트 등록 완료")

        # 🔍 DEBUG: Print all registered routes
        print("\n📋 등록된 라우트 목록:")
        for rule in app.url_map.iter_rules():
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            print(f"  {methods:20s} {rule.rule}")
        print()
        
    except Exception as e:
        print(f"⚠️ API 블루프린트 로드 실패: {e}")
        print(f"   작업 디렉토리: {os.getcwd()}")
        print(f"   BASE_DIR: {BASE_DIR}")
        import traceback
        traceback.print_exc()


def register_error_handlers(app):
    """에러 핸들러 등록"""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        # SECURITY: Safely handle database rollback with error handling
        try:
            if db.session.is_active:
                db.session.rollback()
        except Exception as rollback_error:
            # Log rollback failure but don't expose details to client
            print(f"Error during rollback: {rollback_error}")
        return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request', 'message': str(error)}), 400


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    print("=" * 50)
    print("🚀 SafeFall Backend Server Starting...")
    print(f"📍 Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"🌐 CORS Origins: {app.config['CORS_ORIGINS']}")
    print(f"💾 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG'],
        threaded=True
    )