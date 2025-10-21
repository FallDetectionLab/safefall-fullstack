# 🚀 SafeFall 로컬 맥북 퀵스타트 가이드

## ✅ 현재 상태
- 백엔드: localhost:5001 (정상 작동 ✅)
- 프론트엔드: localhost:5173 (로그인 성공 ✅)
- 데이터베이스: SQLite 연결됨 ✅

---

## 🎯 빠른 시작 (3단계)

### 1단계: 기본 사용자 생성 (최초 1회만)

```bash
cd /Users/choihyunjin/poly/safefall-fullstack-main
chmod +x init_setup.sh
./init_setup.sh
```

**생성되는 기본 계정:**
- **사용자 ID**: `1` ← 로그인할 때 이걸 입력!
- 사용자명(username): `Administrator` (표시용)
- **비밀번호**: `admin123`

**⚠️ 중요:** 로그인할 때는 **ID(`1`)를 사용**합니다 (username이 아님!)

---

### 2단계: 서버 실행

```bash
# 백엔드와 프론트엔드 동시 실행
./start_local_mac.sh

# 또는 개별 실행
# 백엔드만: ./start_backend_only.sh
# 프론트엔드만: cd Front && npm run dev
```

---

### 3단계: 접속 및 테스트

**웹 브라우저:**
- http://localhost:5173 (프론트엔드)
- **로그인 ID**: `1`
- **비밀번호**: `admin123`

**API 테스트 (터미널):**
```bash
# 인증 포함 전체 테스트
chmod +x test_api_with_auth.sh
./test_api_with_auth.sh
# 입력: 1 / admin123 (또는 엔터키로 기본값 사용)
```

---

## 📍 주요 엔드포인트

### 인증 불필요 (브라우저에서 바로 접속 가능)
```
✅ http://localhost:5001/health
✅ http://localhost:5001/api/stream/session/status
✅ http://localhost:5001/api/stream/buffer/status
✅ http://localhost:5001/api/stream/frame/latest
```

### 인증 필요 (로그인 후 JWT 토큰 필요)
```
🔐 http://localhost:5001/api/dashboard/stats
🔐 http://localhost:5001/api/incidents/list
🔐 http://localhost:5001/api/dashboard/recent-videos
🔐 http://localhost:5001/api/auth/me
```

---

## 🛠 유용한 스크립트

### 전체 시스템 실행
```bash
./start_local_mac.sh
```

### 백엔드만 실행 (디버깅용)
```bash
./start_backend_only.sh
```

### API 간단 테스트 (인증 없음)
```bash
./test_api.sh
```

### API 전체 테스트 (인증 포함)
```bash
./test_api_with_auth.sh
```

### 기본 사용자 초기화
```bash
./init_setup.sh
```

---

## 🔧 문제 해결

### 포트가 이미 사용 중
```bash
# 5001 포트 확인 및 종료
lsof -ti:5001
kill -9 $(lsof -ti:5001)

# 5173 포트 (프론트엔드)
lsof -ti:5173
kill -9 $(lsof -ti:5173)
```

### AirPlay 포트 충돌 (5000번)
macOS 설정 → 일반 → AirDrop 및 Handoff → AirPlay Receiver 끄기

### 가상환경 재생성
```bash
cd Back
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 데이터베이스 초기화
```bash
cd Back
rm -f instance/safefall.db
python init_default_user.py
```

---

## 📊 시스템 상태 확인

### Health Check
```bash
curl http://localhost:5001/health | python3 -m json.tool
```

**정상 응답:**
```json
{
  "status": "healthy",
  "checks": {
    "database": "connected",
    "streaming_blueprint": "registered",
    "videos_directory": "accessible"
  }
}
```

### 로그인 테스트
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"id":"1","password":"admin123"}' \
  | python3 -m json.tool
```

**성공 응답:**
```json
{
  "access_token": "eyJ...",
  "user": {
    "id": "1",
    "username": "Administrator"
  }
}
```

---

## 🔑 로그인 필드 설명

SafeFall은 `id`와 `username`을 구분합니다:

| 필드 | 용도 | 예시 |
|------|------|------|
| **id** | 로그인용 고유 식별자 | `1`, `admin`, `user123` |
| **username** | 화면 표시용 이름 | `Administrator`, `홍길동` |

**로그인할 때는 항상 `id`를 사용하세요!**

```json
// ✅ 올바른 로그인 요청
{
  "id": "1",
  "password": "admin123"
}

// ❌ 잘못된 로그인 요청
{
  "username": "Administrator",  // username은 로그인에 사용 안 됨!
  "password": "admin123"
}
```

---

## 📱 라즈베리파이 연결 설정

라즈베리파이에서 영상을 보낼 때:

```python
BACKEND_URL = "http://<맥북-IP>:5001"
```

**맥북 IP 확인:**
```bash
ifconfig en0 | grep "inet " | awk '{print $2}'
```

---

## 🎯 다음 단계

1. ✅ 백엔드 정상 작동 확인
2. ✅ 프론트엔드 로그인 성공
3. ⬜ 라즈베리파이 연동 테스트
4. ⬜ 실시간 영상 스트리밍 테스트
5. ⬜ 사고 감지 및 알림 테스트

---

## 📝 메모

- 백엔드 포트: 5000 → 5001 (AirPlay 충돌 회피)
- **기본 사용자 ID**: `1`
- **기본 비밀번호**: `admin123`
- JWT 토큰 유효기간: 1시간
- 비디오 버퍼: 30초 (900 프레임 @ 30fps)

---

## 🆘 자주 묻는 질문

### Q: 로그인이 안 돼요!
A: `username`이 아닌 `id`를 입력하세요. 기본값은 `1`입니다.

### Q: 프론트엔드에서는 뭘 입력하나요?
A: 로그인 화면에서:
- ID/사용자명 입력란: `1` 입력
- 비밀번호: `admin123`

### Q: 사용자를 추가하고 싶어요
A: `/api/auth/register` 엔드포인트 사용:
```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "id": "user2",
    "username": "김철수",
    "password": "mypassword",
    "email": "user2@example.com"
  }'
```

---

마지막 업데이트: 2025-05-02
