# SafeFall - 통합 버전

낙상·고립 대응 IoT 솔루션 (라즈베리파이 엣지 컴퓨팅 버전)

## 🎯 주요 특징

- **엣지 AI**: 라즈베리파이에서 YOLO 모델 실행
- **실시간 감지**: 낙상 발생 즉시 서버에 알림
- **영상 자동 저장**: 사고 발생 전후 30초 영상 자동 저장
- **웹 대시보드**: React 기반 실시간 모니터링
- **확장 가능**: 여러 대의 라즈베리파이 동시 연결 지원

---

## 📁 디렉토리 구조

```
safefallFullstack-main/
├── Back/                   # Flask 백엔드 서버
│   ├── api/               # API 엔드포인트
│   │   ├── auth.py       # 인증
│   │   ├── streaming.py  # 스트리밍
│   │   ├── incidents.py  # 사고 관리
│   │   ├── dashboard.py  # 대시보드 (NEW!)
│   │   ├── videos.py     # 비디오 관리 (NEW!)
│   │   └── notifications.py
│   ├── models.py         # DB 모델
│   ├── config.py         # 설정
│   └── app.py            # 메인 앱
│
├── Front/                 # React 프론트엔드
│   └── (React 앱)
│
├── RASP/                  # 라즈베리파이 클라이언트
│   ├── pi_client.py      # 메인 클라이언트 (멀티스레드)
│   ├── detector.py       # YOLO 낙상 감지
│   ├── camera.py         # 카메라 제어 (rpicam-vid)
│   ├── uploader.py       # 백엔드 통신
│   └── config.py         # 설정
│
└── test_integration.py    # 통합 테스트 스크립트 (NEW!)
```

---

## 🚀 빠른 시작

### 1. 백엔드 설정

```bash
cd Back

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 기본 사용자 생성 (필수!)
python init_default_user.py

# 서버 실행
python app.py
```

백엔드가 `http://localhost:5000`에서 실행됩니다.

**기본 계정 정보:**
- ID: `admin`
- Password: `admin123`

⚠️ **보안 경고**: 프로덕션 환경에서는 반드시 비밀번호를 변경하세요!

### 2. 프론트엔드 설정

```bash
cd Front

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

프론트엔드가 `http://localhost:5173`에서 실행됩니다.

### 3. 라즈베리파이 설정

```bash
cd RASP

# 의존성 설치
pip install ultralytics opencv-python requests python-dotenv

# YOLO 모델 다운로드
python download_model.py

# .env 파일 생성
cat > .env << EOF
BACKEND_URL=http://YOUR_SERVER_IP:5000
DEVICE_ID=pi-01
YOLO_MODEL_PATH=models/yolo11n.pt
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_FPS=30
CONFIDENCE_THRESHOLD=0.5
ASPECT_RATIO_THRESHOLD=1.5
EOF

# 클라이언트 실행
python pi_client.py
```

---

## 🧪 통합 테스트

백엔드를 실행한 후, 라즈베리파이 없이 전체 시스템을 테스트할 수 있습니다:

```bash
# 루트 디렉토리에서 실행
python test_integration.py
```

**테스트 항목:**
1. ✅ 백엔드 연결
2. ✅ 스트리밍 세션 시작
3. ✅ 프레임 업로드 (30개)
4. ✅ 낙상 사고 신고
5. ✅ 사고 목록 조회
6. ✅ 대시보드 통계
7. ✅ 비디오 동기화
8. ✅ 스트리밍 상태 확인

---

## 📡 API 엔드포인트

### 🔐 인증 (Authentication)
- `POST /api/auth/login` - 로그인
- `POST /api/auth/register` - 회원가입

### 📹 스트리밍 (Streaming)
- `POST /api/stream/session/start` - 세션 시작
- `POST /api/stream/session/stop` - 세션 종료
- `POST /api/stream/upload` - 프레임 업로드
- `GET /api/stream/mjpeg` - MJPEG 스트림
- `GET /api/stream/frame/latest` - 최신 프레임
- `GET /api/stream/session/status` - 세션 상태

### 🚨 사고 관리 (Incidents)
- `POST /api/incidents/report` - 사고 신고 (인증 불필요)
- `GET /api/incidents/list` - 사고 목록
- `GET /api/incidents/<id>` - 사고 상세
- `GET /api/incidents/<id>/video` - 사고 영상
- `GET /api/incidents/<id>/thumbnail` - 썸네일
- `PATCH /api/incidents/<id>/check` - 사고 확인
- `DELETE /api/incidents/<id>` - 사고 삭제

### 📊 대시보드 (Dashboard) **NEW!**
- `GET /api/dashboard/stats` - 통계
- `GET /api/dashboard/recent-videos` - 최근 영상
- `GET /api/dashboard/incidents/summary` - 사고 요약
- `GET /api/dashboard/stream/status` - 스트리밍 상태

### 🎬 비디오 관리 (Videos) **NEW!**
- `GET /api/videos/saved` - 저장된 영상 목록
- `GET /api/videos/recent` - 최근 영상
- `GET /api/videos/<id>` - 영상 상세
- `PUT /api/videos/<id>/status` - 영상 상태 업데이트
- `POST /api/videos/sync` - 파일시스템 동기화

---

## 🔧 시스템 흐름

### 1. 정상 스트리밍
```
라즈베리파이                  백엔드 서버
    |                            |
    |-- 카메라 캡처 (30fps) ---->|
    |                            |
    |-- 로컬 YOLO 감지           |
    |   (낙상 여부 판단)          |
    |                            |
    |-- 프레임 전송 (10fps) ---->|
    |                            |--> 순환 버퍼 저장 (30초)
    |                            |--> MJPEG 스트림 제공
    |                            |--> 프론트엔드로 전송
```

### 2. 낙상 감지 시
```
라즈베리파이                  백엔드 서버              데이터베이스
    |                            |                         |
    |-- 낙상 감지 (aspect_ratio >1.5)
    |   confidence > 0.5         |                         |
    |                            |                         |
    |-- POST /api/incidents/report
    |   {                        |                         |
    |     incident_type: "fall", |                         |
    |     confidence: 0.95,      |                         |
    |     user_id: "admin"       |                         |
    |   }                        |                         |
    |                            |                         |
    |                            |--> 순환 버퍼에서         |
    |                            |    전후 30초 프레임 추출  |
    |                            |                         |
    |                            |--> MP4 영상 생성        |
    |                            |    (videos/ 폴더)       |
    |                            |                         |
    |                            |--> 썸네일 생성          |
    |                            |                         |
    |                            |--> Incident 테이블 저장 ->|
    |                            |                         |
    |<-- 201 Created (사고 ID)    |                         |
    |                            |                         |
    |-- 5초 쿨다운               |                         |
```

---

## ⚙️ 설정 파일

### 백엔드 (.env - 선택사항)
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-change-this
DATABASE_URI=sqlite:///instance/safefall.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 라즈베리파이 (RASP/.env - 필수)
```env
# 백엔드 서버 주소 (반드시 변경!)
BACKEND_URL=http://192.168.0.100:5000

# 디바이스 ID
DEVICE_ID=pi-01

# YOLO 모델 경로
YOLO_MODEL_PATH=models/yolo11n.pt

# 카메라 설정
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_FPS=30

# 낙상 감지 설정
CONFIDENCE_THRESHOLD=0.5      # YOLO 신뢰도 임계값
ASPECT_RATIO_THRESHOLD=1.5    # 가로/세로 비율 (누워있음 판단)
```

---

## 🔍 문제 해결

### 1. "User admin does not exist" 오류
```bash
cd Back
python init_default_user.py
```

### 2. 프레임이 백엔드에 도착하지 않음
**확인 사항:**
- 라즈베리파이의 `BACKEND_URL`이 정확한지 확인
- 백엔드 서버가 실행 중인지 확인
- 방화벽에서 포트 5000 허용 확인
- 같은 네트워크에 있는지 확인

**테스트 방법:**
```bash
# 라즈베리파이에서 백엔드 연결 테스트
curl http://YOUR_SERVER_IP:5000/health
```

### 3. 비디오가 저장되지 않음

**원인 1: 버퍼에 프레임 부족**
- 최소 30초 이상 스트리밍해야 영상 생성 가능
- 프레임 업로드가 정상적으로 되고 있는지 확인

**원인 2: 디렉토리 권한 문제**
```bash
# videos 디렉토리 생성 및 권한 확인
cd Back
mkdir -p videos
chmod 755 videos
```

**원인 3: 디스크 공간 부족**
```bash
df -h  # 디스크 사용량 확인
```

**디버깅:**
```bash
# 백엔드 로그에서 확인
# "📦 버퍼에서 N 프레임 추출" 메시지가 있는지 확인
```

### 4. YOLO 모델 로드 실패 (라즈베리파이)
```bash
cd RASP
python download_model.py

# 수동 다운로드
mkdir -p models
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11n.pt -O models/yolo11n.pt
```

### 5. 카메라가 인식되지 않음 (라즈베리파이)
```bash
# 카메라 모듈 확인
rpicam-vid --list-cameras

# 카메라 테스트
rpicam-vid -t 5000 -o test.h264
```

### 6. DB에 영상이 저장되지 않음

**확인 방법:**
```bash
cd Back

# Python 인터프리터 실행
python

# DB 내용 확인
>>> from app import create_app
>>> from models import db, Incident
>>> app = create_app()
>>> with app.app_context():
...     incidents = Incident.query.all()
...     for inc in incidents:
...         print(f"ID: {inc.id}, 파일: {inc.video_path}, 시간: {inc.detected_at}")
```

**해결 방법:**
1. `init_default_user.py` 실행 확인
2. 라즈베리파이에서 `user_id: 'admin'` 전송 확인
3. `/api/incidents/report` 엔드포인트 응답 확인

---

## 📊 성능 최적화

### 네트워크 대역폭 절약
- ✅ 라즈베리파이에서 YOLO 실행 (엣지 컴퓨팅)
- ✅ 전송 FPS 조절 (기본: 10fps, 캡처: 30fps)
- ✅ JPEG 품질 설정 (기본: 85)
- ✅ 낙상 감지 시에만 알림 전송

**예상 대역폭:**
- 1280x720 JPEG @ 10fps ≈ 1-2 MB/s
- 640x480 JPEG @ 10fps ≈ 0.5-1 MB/s

### 라즈베리파이 CPU 사용률
- YOLO 모델: yolo11n (nano) 사용 - 가장 가벼움
- 멀티스레드 처리 (캡처/전송/감지 분리)
- 큐 기반 프레임 버퍼링
- FPS 제어로 과부하 방지

**권장 하드웨어:**
- Raspberry Pi 4 (4GB 이상)
- Camera Module 3 또는 호환 카메라

### 서버 리소스
- 순환 버퍼 (30초분 프레임만 메모리 유지)
- 영상 압축 (MP4/H.264)
- SQLite → PostgreSQL (프로덕션 권장)
- 오래된 영상 자동 삭제 스크립트

---

## 🔐 보안 고려사항

### 1. 기본 비밀번호 변경 (필수!)
```python
# 백엔드 서버에서
from app import create_app
from models import db, User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(id='admin').first()
    admin.set_password('강력한비밀번호')
    db.session.commit()
```

### 2. JWT 시크릿 키 설정
```bash
# Back/.env
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

### 3. HTTPS 사용 (프로덕션)
```bash
# Nginx + Let's Encrypt
sudo apt install nginx certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 4. 방화벽 설정
```bash
# 백엔드 서버
sudo ufw allow 5000/tcp  # Flask
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## 📈 현재 진행 상황

### ✅ 완료된 기능
1. ✅ 라즈베리파이에 YOLO11 모델 탑재
2. ✅ 낙상 감지 (aspect ratio 기반)
3. ✅ 사고 영상 자동 저장 (MP4)
4. ✅ 썸네일 자동 생성
5. ✅ 백엔드-프론트엔드 통신
6. ✅ 회원가입/로그인 기능
7. ✅ 데이터베이스 영상 저장 **NEW!**
8. ✅ 대시보드 API **NEW!**
9. ✅ 비디오 관리 API **NEW!**
10. ✅ 통합 테스트 스크립트 **NEW!**

### 🚧 진행 중
1. 🔄 실시간 알림 시스템
2. 🔄 프론트엔드 실시간 연동
3. 🔄 회원가입 후 자동 로그인

### 📝 개선 필요
1. ⚠️ 영상 전송 딜레이 (현재 10초) → 목표 3초 이하
2. ⚠️ 프레임 드롭 현상 개선
3. ⚠️ YOLO 모델 추가 학습 (정확도 향상)

---

## 📝 추가 기능 (향후 개발)

- [ ] 실시간 알림 (Firebase Cloud Messaging)
- [ ] 이메일/SMS 알림
- [ ] 다중 사용자 지원 강화
- [ ] 영상 클라우드 저장 (AWS S3, Google Cloud Storage)
- [ ] 모바일 앱 (React Native)
- [ ] 고립 감지 (열감지 센서 연동)
- [ ] 통계 대시보드 고도화
- [ ] AI 모델 정확도 개선 (커스텀 학습)
- [ ] 다양한 사고 유형 감지 (쓰러짐, 비명 등)
- [ ] 사용자별 알림 설정
- [ ] 영상 압축 최적화

---

## 🤝 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이선스

This project is licensed under the MIT License.

---

## 👥 팀원

- **박길웅** - 프로젝트 매니저, IoT 감지 데이터 수집 및 분석 플랫폼
- **안준수** - 실시간 감지 기록 DB, AI 영상 분석 서버 모듈
- **이동민** - 상태 모니터링 웹 인터페이스, AI 영상 분석 서버 모듈
- **이동환** - IoT 감지 데이터 수집 및 분석 플랫폼
- **최현진** - IoT 감지 데이터 수집 및 분석 플랫폼, 하드웨어 설계

---

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

---

## 🎓 프로젝트 정보

- **학교**: 한국폴리텍대학
- **학과**: AI 융합소프트웨어
- **지도교수**: 김성수
- **작성일**: 2025. 04. 29
- **최종 수정**: 2025. 10. 15

---

**SafeFall** - Making homes safer with AI-powered fall detection 🏠🤖
