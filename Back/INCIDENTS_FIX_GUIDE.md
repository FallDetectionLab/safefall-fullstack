# SafeFall Backend - incidents.py 수정 가이드

## 문제: incident_lock 타임아웃

`with incident_lock:` 블록이 전체 영상 저장 프로세스를 블로킹하여 타임아웃 발생

---

## 해결책 1: Lock 타임아웃 추가 (빠른 수정)

### 수정 위치: Line 186

**기존 코드:**
```python
with incident_lock:
    video_path = None
    thumbnail_path = None
    # ... 영상 저장 로직
```

**수정 코드:**
```python
# Lock 획득 시도 (5초 타임아웃)
if not incident_lock.acquire(timeout=5):
    print("⚠️ Server busy processing another incident")
    return jsonify({
        'error': 'Server busy',
        'message': 'Another incident is being processed. Please try again.'
    }), 503

try:
    video_path = None
    thumbnail_path = None
    
    # ... 기존 영상 저장 로직 ...
    
finally:
    # Lock 해제 (반드시 실행)
    incident_lock.release()
```

---

## 해결책 2: 비동기 처리 (권장)

영상 저장을 백그라운드 스레드로 처리

```python
import threading

def save_incident_video_async(data, detected_at, user_id, incident_type, confidence):
    """백그라운드에서 영상 저장"""
    try:
        # 기존 영상 저장 로직을 여기로 이동
        pass
    except Exception as e:
        print(f"❌ 백그라운드 영상 저장 실패: {e}")

@incidents_bp.route('/report', methods=['POST'])
def report_incident():
    # ... 데이터 검증 ...
    
    # 즉시 응답 반환
    response_data = {
        'status': 'accepted',
        'message': 'Incident report received, video will be saved shortly'
    }
    
    # 백그라운드 스레드로 영상 저장
    thread = threading.Thread(
        target=save_incident_video_async,
        args=(data, detected_at, user_id, incident_type, confidence)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify(response_data), 202  # 202 Accepted
```

---

## 적용 방법:

### 1. 파일 백업:
```bash
cd /opt/safefallFullstack-main/Back
cp api/incidents.py api/incidents.py.backup.$(date +%Y%m%d_%H%M%S)
```

### 2. 파일 수정:
```bash
nano api/incidents.py
```

### 3. Line 186 부근 수정:
- `with incident_lock:` 찾기 (Ctrl + W)
- 위 "수정 코드"로 교체

### 4. 저장 및 재시작:
```bash
# 저장: Ctrl + O, Enter, Ctrl + X

# 서비스 재시작
sudo systemctl restart safefall-backend

# 로그 확인
sudo journalctl -u safefall-backend -f
```

---

## 테스트:

```bash
curl -X POST http://localhost:8000/api/incidents/report \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "pi-01",
    "incident_type": "fall",
    "detected_at": "2025-10-21T03:44:06Z",
    "confidence": 0.85,
    "user_id": "admin"
  }' \
  --max-time 10
```

**예상 응답:**
- 해결책 1: `{"status": "success", "message": "Incident recorded"}`
- 해결책 2: `{"status": "accepted", "message": "Incident report received"}`

---

**작성: 2025-10-21**
**문제: Lock timeout causing 500 errors**
**해결: Lock timeout + async processing**
