# 🔧 CORS 에러 해결 완료!

## 📋 문제 상황
```
Access to XMLHttpRequest at 'http://localhost:5001/api/stream/live' 
from origin 'http://localhost:5174' has been blocked by CORS policy
```

## ✅ 해결한 내용

### 1. `/api/stream/live` 엔드포인트 추가
**파일**: `Back/api/streaming.py`

새로운 엔드포인트 추가:
```python
@streaming_bp.route('/live', methods=['GET'])
def get_live_stream():
    """실시간 스트림 정보 반환"""
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
        }
    })
```

### 2. CORS 설정 업데이트
**파일**: `Back/config.py`

포트 5174 추가:
```python
CORS_ORIGINS = 'http://localhost:5173,http://localhost:5174,...'
```

## 🚀 적용 방법

### 방법 1: 빠른 재시작 (권장)
```bash
chmod +x restart_backend.sh
./restart_backend.sh
```

### 방법 2: 수동 재시작
```bash
# 기존 프로세스 종료
lsof -ti:5001 | xargs kill -9

# 백엔드 재시작
cd Back
source venv/bin/activate
python app.py
```

## ✅ 테스트

백엔드 재시작 후 브라우저에서 테스트:

```
http://localhost:5001/api/stream/live
```

**예상 응답**:
```json
{
  "success": true,
  "streamUrl": "http://localhost:5001",
  "status": "offline",
  "quality": "720p",
  "type": "mjpeg",
  "endpoints": {
    "mjpeg": "http://localhost:5001/api/stream/mjpeg",
    "latest_frame": "http://localhost:5001/api/stream/frame/latest",
    "hls_playlist": "http://localhost:5001/api/stream/hls/playlist.m3u8"
  },
  "active_session": false,
  "has_frames": false
}
```

## 📱 프론트엔드 확인

재시작 후 프론트엔드(http://localhost:5174)에서:
1. 로그인
2. 대시보드 페이지 접속
3. CORS 에러 없이 화면 표시 확인

## 🔍 문제가 계속되면?

### 1. 백엔드 로그 확인
```bash
# 백엔드 터미널에서 다음 로그 확인:
📋 등록된 라우트 목록:
  GET                  /api/stream/live  # ← 이게 있어야 함
```

### 2. 브라우저 콘솔 확인
```
F12 → Console 탭
- CORS 에러가 사라졌는지 확인
- 네트워크 탭에서 /api/stream/live 요청 상태 확인
```

### 3. CORS 헤더 확인
```bash
curl -H "Origin: http://localhost:5174" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS \
  http://localhost:5001/api/stream/live -v
```

## 📝 변경 파일 요약

1. `Back/api/streaming.py` - `/live` 엔드포인트 추가
2. `Back/config.py` - CORS에 포트 5174 추가
3. `restart_backend.sh` - 빠른 재시작 스크립트 생성

---

생성일: 2025-10-21
