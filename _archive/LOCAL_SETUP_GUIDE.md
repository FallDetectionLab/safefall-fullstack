# 🖥️ SafeFall 로컬 개발 환경 가이드

## ✅ 설정 완료!

`.env` 파일과 실행 스크립트가 자동으로 생성되었습니다.

---

## 🚀 실행 방법

### 방법 1: 스크립트 사용 (추천)

**터미널 1 - 백엔드 실행:**
```bash
cd Back
chmod +x start_local.sh
./start_local.sh
```

**터미널 2 - 프론트엔드 실행:**
```bash
cd Front
chmod +x start_local.sh
./start_local.sh
```

### 방법 2: 수동 실행

**백엔드:**
```bash
cd Back
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**프론트엔드:**
```bash
cd Front
npm install
npm run dev
```

---

## 🌐 접속 주소

| 서비스 | URL | 용도 |
|--------|-----|------|
| 백엔드 | http://localhost:5000 | API 서버 |
| 백엔드 Health | http://localhost:5000/health | 서버 상태 확인 |
| 프론트엔드 | http://localhost:5173 | 웹 인터페이스 |

---

## 📦 필요한 프로그램

### macOS:
```bash
# Homebrew 설치 (없는 경우)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.12 설치
brew install python@3.12

# Node.js 설치
brew install node

# 확인
python3 --version  # Python 3.12.x
node --version     # v20.x.x
npm --version      # 10.x.x
```

---

## 🔧 환경 설정 파일

### Back/.env (백엔드)
```env
FLASK_ENV=development
DEBUG=True
VITE_BACKEND_URL=http://localhost:5000
```
✅ 자동 생성됨

### Front/.env (프론트엔드)
```env
VITE_BACKEND_URL=http://localhost:5000
VITE_API_BASE_URL=http://localhost:5000/api
VITE_DEBUG_MODE=true
```
✅ 자동 생성됨

---

## ✅ 작동 확인

### 1. 백엔드 확인
```bash
curl http://localhost:5000/health
```

**응답:**
```json
{
  "status": "healthy",
  "message": "SafeFall Backend Running"
}
```

### 2. 프론트엔드 확인
브라우저에서 http://localhost:5173 접속
- 로그인 페이지 표시 확인

### 3. 통신 확인
- F12 → Network 탭
- API 요청이 `localhost:5000`으로 가는지 확인

---

## 🐛 문제 해결

### 문제: 백엔드 실행 시 "Address already in use"

**해결:**
```bash
# 5000 포트 사용 중인 프로세스 확인
lsof -i :5000

# 프로세스 종료
kill -9 [PID]
```

### 문제: 프론트엔드 실행 시 "EADDRINUSE"

**해결:**
```bash
# 5173 포트 사용 중인 프로세스 확인
lsof -i :5173

# 프로세스 종료
kill -9 [PID]
```

### 문제: Python 가상환경 활성화 안 됨

**해결:**
```bash
cd Back
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 문제: npm install 실패

**해결:**
```bash
cd Front
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

---

## 📂 프로젝트 구조

```
safefall-fullstack-main/
├── Back/               # 백엔드 (Flask)
│   ├── .env           # 환경 변수 ✅
│   ├── start_local.sh # 실행 스크립트 ✅
│   ├── app.py         # 메인 앱
│   └── venv/          # 가상환경 (자동 생성)
├── Front/             # 프론트엔드 (React + Vite)
│   ├── .env           # 환경 변수 ✅
│   ├── start_local.sh # 실행 스크립트 ✅
│   └── node_modules/  # 의존성 (자동 생성)
└── RASP/              # 라즈베리파이 코드
```

---

## 🔄 AWS 서버와의 차이점

| 설정 | 로컬 개발 | AWS 서버 |
|------|----------|----------|
| 백엔드 URL | http://localhost:5000 | http://43.203.245.90:8000 |
| 프론트엔드 URL | http://localhost:5173 | http://safefall2.s3-website... |
| DEBUG 모드 | True | False |
| 데이터베이스 | SQLite (로컬) | SQLite (서버) |

---

## 🎯 다음 단계

### 1. 로컬에서 개발
- 코드 수정
- 테스트

### 2. Git Push
```bash
git add .
git commit -m "feat: 새 기능 추가"
git push origin main
```

### 3. AWS 서버에서 업데이트
```bash
ssh ubuntu@43.203.245.90
cd /opt/safefallFullstack-main
git pull
sudo systemctl restart safefall-backend
```

---

## 📞 도움말

- 백엔드 로그: 터미널에서 실시간 확인
- 프론트엔드 로그: 브라우저 개발자 도구 (F12) → Console
- API 테스트: http://localhost:5000/health

---

**마지막 업데이트: 2025년 10월 20일**
