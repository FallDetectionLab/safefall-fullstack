# SafeFall 로컬 개발 환경 설정 가이드

## 📋 사전 요구사항

- Python 3.11+
- Node.js 18+
- 라즈베리파이 (카메라 연결)

---

## 🚀 빠른 시작

### 1. 프로젝트 클론
```bash
git clone https://github.com/FallDetectionLab/safefall-fullstack.git
cd safefall-fullstack
```

### 2. 백엔드 설정

```bash
cd Back

# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (맥/리눅스)
source venv/bin/activate

# Windows
# venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 열어서 필요한 값 수정

# DB 초기화
python init_default_user.py

# 서버 실행
python app.py
```

서버 실행 확인: http://localhost:5001

### 3. 프론트엔드 설정

```bash
cd ../Front

# 패키지 설치
npm install

# 환경변수 설정
# .env 파일이 이미 있음 (VITE_BACKEND_URL=http://localhost:5001)

# 개발 서버 실행
npm run dev
```

프론트엔드 확인: http://localhost:5173

### 4. 라즈베리파이 설정

```bash
# 라즈베리파이에서
cd RASP

# config.py 수정
nano config.py
# BACKEND_URL을 로컬 맥북 IP로 변경
# BACKEND_URL = "http://192.168.0.xxx:5001"

# 실행
python pi_client.py
```

---

## 📌 주요 엔드포인트

### 백엔드 (포트 5001)
- `GET /` - Health check
- `GET /api/incidents/list` - 영상 목록
- `GET /api/incidents/{id}/video` - 영상 스트리밍
- `GET /api/stream/mjpeg` - 실시간 카메라 스트림
- `POST /api/incidents/report` - 낙상 신호 수신

### 프론트엔드 (포트 5173)
- `/` - 로그인 전 화면
- `/login` - 로그인
- `/dashboard` - 대시보드 (실시간 영상)
- `/history` - 영상 목록
- `/video/:id` - 영상 상세

---

## 🔧 문제 해결

### 비디오가 재생 안 됨
1. 백엔드 포트 확인: `http://localhost:5001`
2. 비디오 URL 형식: `/api/incidents/{id}/video`
3. 브라우저 콘솔(F12) 확인

### 실시간 스트림 안 보임
1. 라즈베리파이가 실행 중인지 확인
2. BACKEND_URL이 올바른 IP인지 확인
3. 방화벽 설정 확인

### 가상환경 활성화 안 됨
```bash
# 맥/리눅스
source venv/bin/activate

# 터미널 앞에 (venv) 표시되면 성공
```

---

## 📚 추가 문서

- [백엔드 API 문서](./Back/README.md)
- [프론트엔드 개발 가이드](./Front/README.md)
- [라즈베리파이 설정](./RASP/README.md)

---

## 👥 기여자

AI 융합소프트웨어 - 캡스톤 프로젝트 팀
- 박길웅
- 안준수
- 이동민
- 이동환
- 최현진
