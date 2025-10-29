# 🚀 SafeFall 백엔드 완전 재설정 가이드

작성일: 2025-10-21  
작성자: 최현진

---

## 📋 목차

1. [EC2 접속](#1-ec2-접속)
2. [백엔드 디렉토리 이동](#2-백엔드-디렉토리-이동)
3. [가상환경 활성화](#3-가상환경-활성화)
4. [환경변수 설정](#4-환경변수-설정)
5. [의존성 설치](#5-의존성-설치)
6. [데이터베이스 초기화](#6-데이터베이스-초기화)
7. [필수 디렉토리 생성](#7-필수-디렉토리-생성)
8. [systemd 서비스 설정](#8-systemd-서비스-설정)
9. [서비스 재시작](#9-서비스-재시작)
10. [로그 확인](#10-로그-확인)
11. [테스트](#11-테스트)
12. [트러블슈팅](#12-트러블슈팅)
13. [자주 쓰는 명령어](#13-자주-쓰는-명령어-모음)

---

## 1️⃣ EC2 접속

### 맥북에서 실행:
```bash
ssh -i /Users/choihyunjin/poly/safefall-backend/keypair-seoul.pem ubuntu@43.203.245.90
```

### 접속 확인:
```bash
# 현재 위치 확인
pwd

# 시스템 정보 확인
uname -a
```

---

## 2️⃣ 백엔드 디렉토리 이동

```bash
cd /opt/safefallFullstack-main/Back

# 현재 디렉토리 확인
ls -la
```

---

## 3️⃣ 가상환경 활성화

```bash
# 가상환경 활성화
source venv/bin/activate

# 활성화 확인 (프롬프트에 (venv) 표시됨)
# 예: (venv) ubuntu@ip-10-0-0-91:/opt/safefallFullstack-main/Back$

# Python 버전 확인
python --version

# 설치된 패키지 확인
pip list
```

### 가상환경 비활성화 (필요시):
```bash
deactivate
```

---

## 4️⃣ 환경변수 설정

### .env 파일 생성/수정:
```bash
nano .env
```

### 필수 내용 입력:
```env
# ============================================
# SafeFall Backend 환경 변수
# ============================================

# Database
DATABASE_URL=sqlite:///safefall.db

# Security
SECRET_KEY=your-secret-key-here-change-this-in-production-2025
JWT_SECRET_KEY=your-jwt-secret-key-here-change-this-in-production-2025

# Server
FLASK_ENV=production
FLASK_DEBUG=False

# File upload
UPLOAD_FOLDER=/opt/safefallFullstack-main/Back/uploads
MAX_CONTENT_LENGTH=104857600

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/safefall/app.log

# CORS (프론트엔드 도메인)
CORS_ORIGINS=http://safefall2.s3-website.ap-northeast-2.amazonaws.com,http://localhost:5173

# API Settings
API_VERSION=v1
API_PREFIX=/api
```

### 저장 방법:
1. `Ctrl + O` (WriteOut - 저장)
2. `Enter` (파일명 확인)
3. `Ctrl + X` (Exit - 나가기)

### 확인:
```bash
cat .env
```

---

## 5️⃣ 의존성 설치

### requirements.txt 확인:
```bash
cat requirements.txt
```

### 의존성 설치:
```bash
# 전체 설치
pip install -r requirements.txt

# 업그레이드 포함 설치
pip install --upgrade -r requirements.txt
```

### 주요 패키지 개별 설치 (필요시):
```bash
pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install flask-jwt-extended==4.6.0
pip install sqlalchemy==2.0.23
pip install python-dotenv==1.0.0
pip install gunicorn==21.2.0
pip install requests==2.31.0
pip install pillow==10.1.0
```

### 설치 확인:
```bash
pip list | grep -E "flask|gunicorn|sqlalchemy"
```

---

## 6️⃣ 데이터베이스 초기화

### 기존 DB 백업 (있다면):
```bash
# 백업
cp safefall.db safefall.db.backup.$(date +%Y%m%d_%H%M%S)

# 백업 확인
ls -lh safefall.db*
```

### DB 재생성:
```bash
# 방법 1: Python 명령어로 초기화
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ Database initialized')"

# 방법 2: Python 스크립트 실행 (init_db.py가 있다면)
python init_db.py
```

### DB 확인:
```bash
ls -lh safefall.db
```

---

## 7️⃣ 필수 디렉토리 생성

### uploads 디렉토리:
```bash
# 생성
sudo mkdir -p /opt/safefallFullstack-main/Back/uploads

# 소유권 변경
sudo chown -R ubuntu:ubuntu /opt/safefallFullstack-main/Back/uploads

# 권한 설정
sudo chmod -R 755 /opt/safefallFullstack-main/Back/uploads

# 확인
ls -ld /opt/safefallFullstack-main/Back/uploads
```

### logs 디렉토리:
```bash
# 생성
sudo mkdir -p /var/log/safefall

# 소유권 변경
sudo chown -R ubuntu:ubuntu /var/log/safefall

# 권한 설정
sudo chmod -R 755 /var/log/safefall

# 확인
ls -ld /var/log/safefall
```

### videos 디렉토리 (녹화 영상용):
```bash
# 생성
sudo mkdir -p /opt/safefallFullstack-main/Back/videos

# 소유권 변경
sudo chown -R ubuntu:ubuntu /opt/safefallFullstack-main/Back/videos

# 권한 설정
sudo chmod -R 755 /opt/safefallFullstack-main/Back/videos
```

---

## 8️⃣ systemd 서비스 설정

### 서비스 파일 확인:
```bash
sudo cat /etc/systemd/system/safefall-backend.service
```

### 올바른 서비스 파일 내용:
```ini
[Unit]
Description=SafeFall Backend Service
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/safefallFullstack-main/Back
Environment="PATH=/opt/safefallFullstack-main/Back/venv/bin"
ExecStart=/opt/safefallFullstack-main/Back/venv/bin/gunicorn \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile /var/log/safefall/access.log \
    --error-logfile /var/log/safefall/error.log \
    --log-level info \
    app:create_app()
Restart=always
RestartSec=10
MemoryLimit=2G

[Install]
WantedBy=multi-user.target
```

### 서비스 파일 수정 (필요시):
```bash
sudo nano /etc/systemd/system/safefall-backend.service
```

---

## 9️⃣ 서비스 재시작

### 서비스 파일 변경 후 reload:
```bash
sudo systemctl daemon-reload
```

### 서비스 재시작:
```bash
sudo systemctl restart safefall-backend
```

### 상태 확인:
```bash
sudo systemctl status safefall-backend
```

### 부팅 시 자동 시작 설정:
```bash
sudo systemctl enable safefall-backend
```

### 자동 시작 확인:
```bash
sudo systemctl is-enabled safefall-backend
```

---

## 🔟 로그 확인

### 실시간 로그 모니터링:
```bash
# systemd 로그 실시간
sudo journalctl -u safefall-backend -f

# 최근 100줄
sudo journalctl -u safefall-backend -n 100 --no-pager

# 오늘 로그만
sudo journalctl -u safefall-backend --since today --no-pager
```

### 에러 로그:
```bash
# 실시간
sudo tail -f /var/log/safefall/error.log

# 전체 보기
sudo cat /var/log/safefall/error.log

# 최근 50줄
sudo tail -n 50 /var/log/safefall/error.log
```

### 액세스 로그:
```bash
# 실시간
sudo tail -f /var/log/safefall/access.log

# 최근 100줄
sudo tail -n 100 /var/log/safefall/access.log
```

---

## 1️⃣1️⃣ 테스트

### Health Check:
```bash
# localhost 테스트
curl http://localhost:8000/health

# 공인 IP 테스트
curl http://43.203.245.90:8000/health

# 상세 응답 확인
curl -v http://43.203.245.90:8000/health
```

### API 테스트:

#### 로그인 테스트:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"id":"admin","password":"admin123"}'
```

#### 회원가입 테스트:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"id":"testuser","username":"테스트","password":"test1234"}'
```

#### 영상 목록 조회:
```bash
# JWT 토큰 필요
curl -X GET http://localhost:8000/api/videos \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 포트 리스닝 확인:
```bash
# ss 명령어
sudo ss -tulpn | grep 8000

# lsof 명령어
sudo lsof -i :8000
```

### 프로세스 확인:
```bash
ps aux | grep gunicorn
```

---

## 1️⃣2️⃣ 트러블슈팅

### ❌ 서비스 시작 안 됨

#### 에러 확인:
```bash
# systemd 로그
sudo journalctl -u safefall-backend -n 50 --no-pager

# 에러 로그
sudo tail -n 50 /var/log/safefall/error.log
```

#### 수동 실행으로 에러 확인:
```bash
cd /opt/safefallFullstack-main/Back
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 --timeout 120 app:create_app()

# Ctrl + C로 중지 후 서비스 재시작
```

---

### ❌ 포트 충돌

#### 8000번 포트 사용 프로세스 확인:
```bash
sudo lsof -i :8000
```

#### 프로세스 강제 종료:
```bash
# PID 확인 후
sudo kill -9 <PID>

# 또는 gunicorn 전체 종료
sudo pkill -9 gunicorn
```

---

### ❌ 권한 문제

#### 소유권 확인:
```bash
ls -la /opt/safefallFullstack-main/Back
```

#### 소유권 수정:
```bash
sudo chown -R ubuntu:ubuntu /opt/safefallFullstack-main/Back
sudo chmod -R 755 /opt/safefallFullstack-main/Back
```

#### 디렉토리별 권한:
```bash
# uploads
sudo chown -R ubuntu:ubuntu /opt/safefallFullstack-main/Back/uploads
sudo chmod -R 755 /opt/safefallFullstack-main/Back/uploads

# logs
sudo chown -R ubuntu:ubuntu /var/log/safefall
sudo chmod -R 755 /var/log/safefall
```

---

### ❌ DB 연결 오류

#### DB 파일 확인:
```bash
ls -lh /opt/safefallFullstack-main/Back/safefall.db
```

#### DB 재생성:
```bash
cd /opt/safefallFullstack-main/Back
source venv/bin/activate
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ Database initialized')"
```

---

### ❌ 가상환경 문제

#### 가상환경 재생성:
```bash
cd /opt/safefallFullstack-main/Back

# 기존 가상환경 백업
mv venv venv.backup

# 새 가상환경 생성
python3 -m venv venv

# 활성화
source venv/bin/activate

# 의존성 재설치
pip install --upgrade pip
pip install -r requirements.txt
```

---

### ❌ 메모리 부족

#### 메모리 확인:
```bash
free -h
```

#### 스왑 메모리 추가 (필요시):
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 1️⃣3️⃣ 자주 쓰는 명령어 모음

### 🔄 빠른 재시작 (로그 실시간):
```bash
sudo systemctl restart safefall-backend && sudo journalctl -u safefall-backend -f
```

### 📊 상태 확인:
```bash
sudo systemctl status safefall-backend
```

### 📝 로그 실시간 모니터링:
```bash
sudo journalctl -u safefall-backend -f
```

### 🛑 서비스 중지:
```bash
sudo systemctl stop safefall-backend
```

### ▶️ 서비스 시작:
```bash
sudo systemctl start safefall-backend
```

### 🔁 가상환경 활성화:
```bash
cd /opt/safefallFullstack-main/Back && source venv/bin/activate
```

### 🧪 Health Check:
```bash
curl http://43.203.245.90:8000/health
```

### 📂 디렉토리 이동 원라이너:
```bash
# 백엔드 + 가상환경
cd /opt/safefallFullstack-main/Back && source venv/bin/activate

# 로그 디렉토리
cd /var/log/safefall
```

### 🔍 포트 & 프로세스 확인:
```bash
# 포트 확인
sudo ss -tulpn | grep 8000

# 프로세스 확인
ps aux | grep gunicorn
```

### 📦 패키지 업데이트:
```bash
cd /opt/safefallFullstack-main/Back
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart safefall-backend
```

---

## 📚 추가 참고 자료

### AWS 보안 그룹 설정:
- 포트 8000 → 0.0.0.0/0 (Backend API)
- 포트 80 → 0.0.0.0/0 (HTTP)
- 포트 443 → 0.0.0.0/0 (HTTPS)
- 포트 22 → 허용된 IP만 (SSH)

### 백엔드 URL:
- 공인 IP: `http://43.203.245.90:8000`
- Health Check: `http://43.203.245.90:8000/health`
- API Base: `http://43.203.245.90:8000/api`

### 주요 경로:
- 프로젝트: `/opt/safefallFullstack-main/Back`
- 가상환경: `/opt/safefallFullstack-main/Back/venv`
- 업로드: `/opt/safefallFullstack-main/Back/uploads`
- 로그: `/var/log/safefall`
- DB: `/opt/safefallFullstack-main/Back/safefall.db`
- 서비스: `/etc/systemd/system/safefall-backend.service`

---

## ✅ 체크리스트

설정 완료 확인:

- [ ] EC2 접속 성공
- [ ] 백엔드 디렉토리 확인
- [ ] 가상환경 활성화 확인
- [ ] .env 파일 생성/확인
- [ ] 의존성 설치 완료
- [ ] DB 초기화 완료
- [ ] 필수 디렉토리 생성 (uploads, logs, videos)
- [ ] systemd 서비스 파일 확인
- [ ] 서비스 시작 성공
- [ ] Health check 통과 (localhost)
- [ ] Health check 통과 (공인 IP)
- [ ] AWS 보안 그룹 8000 포트 열림
- [ ] 로그 정상 출력 확인

---

**작성: 2025-10-21**  
**버전: 1.0**  
**문의: SafeFall 개발팀**

---

# 🎉 설정 완료!

모든 단계를 완료하셨다면 백엔드가 정상적으로 작동합니다!

문제가 발생하면 [트러블슈팅](#12-트러블슈팅) 섹션을 참고하세요.
