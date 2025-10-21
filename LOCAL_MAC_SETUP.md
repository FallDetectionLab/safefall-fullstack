# 🍎 SafeFall 로컬 맥북 실행 가이드

## 포트 변경 완료 ✅
- **백엔드 포트**: 5000 → **5001** (AirPlay 충돌 회피)
- **프론트엔드**: 5173 (기본 Vite 포트)

---

## 🚀 빠른 시작

### 1. 초기 설정 (최초 1회만)

```bash
# 백엔드 설정
cd Back
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# 프론트엔드 설정
cd Front
npm install
cd ..
```

### 2. 실행

```bash
# 실행 권한 부여 (최초 1회)
chmod +x start_local_mac.sh

# 실행
./start_local_mac.sh
```

---

## 📍 접속 주소

- **백엔드 API**: http://localhost:5001
- **프론트엔드**: http://localhost:5173
- **Health Check**: http://localhost:5001/health

---

## 🛠 수동 실행 (디버깅용)

### 백엔드만 실행
```bash
cd Back
source venv/bin/activate
python app.py
```

### 프론트엔드만 실행
```bash
cd Front
npm run dev
```

---

## 📝 변경 사항

### `Back/app.py`
```python
# 변경 전: port=5000
# 변경 후: port=5001
app.run(host="0.0.0.0", port=5001, debug=app.config["DEBUG"], threaded=True)
```

### `Front/.env`
```env
VITE_BACKEND_URL=http://localhost:5001
VITE_API_BASE_URL=http://localhost:5001/api
```

---

## ❓ 문제 해결

### 포트가 이미 사용 중인 경우
```bash
# 5001 포트 사용 중인 프로세스 확인
lsof -ti:5001

# 프로세스 종료
kill -9 $(lsof -ti:5001)
```

### AirPlay 포트 충돌 (5000번)
맥 설정 → 일반 → AirDrop 및 Handoff → AirPlay Receiver 끄기

---

## 📦 의존성

### 백엔드
- Python 3.8+
- Flask
- SQLite

### 프론트엔드
- Node.js 16+
- Vite
- React

---

## 🔧 개발 팁

### 백엔드 핫 리로드
```bash
cd Back
source venv/bin/activate
export FLASK_ENV=development
python app.py
```

### 프론트엔드 포트 변경 (필요시)
`Front/vite.config.js`에서 `server.port` 수정

---

## 📱 라즈베리파이 연결

라즈베리파이가 영상을 전송할 때는 다음 주소로 설정:
```
http://<맥북-IP>:5001/api/stream/upload
```

맥북 IP 확인:
```bash
ifconfig en0 | grep inet
```

---

생성일: 2025-05-02
