# SafeFall 프로젝트 배포 체크리스트

## 📋 배포 전 준비사항

### 1. 환경 변수 설정
- [ ] `Back/.env` 파일 생성 및 설정
  - [ ] SECRET_KEY를 랜덤 문자열로 변경
  - [ ] JWT_SECRET_KEY를 랜덤 문자열로 변경
  - [ ] DEBUG=False로 설정
  - [ ] FLASK_ENV=production으로 설정
  - [ ] CORS_ORIGINS에 실제 도메인 추가

- [ ] `Front/.env` 파일 생성 및 설정
  - [ ] VITE_BACKEND_URL을 실제 서버 주소로 변경

### 2. 서버 준비
- [ ] Ubuntu 22.04 LTS 서버 준비 (AWS EC2, DigitalOcean 등)
- [ ] 최소 사양: 2GB RAM, 2 vCPU, 20GB 디스크
- [ ] SSH 접근 가능 확인
- [ ] 도메인 연결 (선택사항)

### 3. 보안 설정
- [ ] 방화벽 규칙 설정 (80, 443, 22 포트)
- [ ] SSH 키 기반 인증 설정
- [ ] 루트 로그인 비활성화
- [ ] fail2ban 설치 및 설정

---

## 🚀 배포 방법

### Option 1: 자동 배포 스크립트 (권장)

```bash
# 1. 서버에 접속
ssh user@your-server-ip

# 2. 프로젝트 업로드
scp -r safefallFullstack-main user@your-server-ip:/opt/

# 또는 Git clone
cd /opt
git clone https://github.com/your-repo/safefallFullstack-main.git

# 3. 배포 스크립트 실행
cd safefallFullstack-main
chmod +x deploy-server.sh
sudo ./deploy-server.sh
```

### Option 2: Docker 배포

```bash
# 1. Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. 프로젝트 디렉토리로 이동
cd safefallFullstack-main

# 4. 환경 변수 설정
cp .env.example .env
nano .env  # 값 수정

# 5. Docker Compose 실행
docker-compose up -d

# 6. 로그 확인
docker-compose logs -f
```

---

## ✅ 배포 후 확인사항

### 1. 서비스 상태 확인
```bash
# Backend 서비스 확인
sudo systemctl status safefall-backend

# Nginx 확인
sudo systemctl status nginx

# 로그 확인
sudo journalctl -u safefall-backend -f
sudo tail -f /var/log/nginx/safefall-*.log
```

### 2. API 테스트
```bash
# Health check
curl http://your-server-ip:5000/health

# 로그인 테스트
curl -X POST http://your-server-ip:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

### 3. Frontend 접근 확인
- [ ] 브라우저에서 `http://your-domain.com` 접속
- [ ] 로그인 기능 테스트
- [ ] 실시간 스트리밍 확인

### 4. 라즈베리파이 연동 확인
- [ ] RASP 폴더의 설정 파일 수정
- [ ] Backend URL을 서버 주소로 변경
- [ ] 테스트 영상 전송 확인

---

## 🔧 설정 파일 위치

```
/opt/safefallFullstack-main/
├── Back/
│   ├── .env                    # Backend 환경 변수
│   ├── app.py                  # Flask 앱
│   └── instance/               # 데이터베이스
├── Front/
│   ├── .env                    # Frontend 환경 변수
│   └── dist/                   # 빌드된 파일
├── nginx-production.conf       # Nginx 설정
└── safefall-backend.service    # Systemd 서비스

/etc/nginx/sites-available/safefall     # Nginx 설정
/etc/systemd/system/safefall-backend.service  # 서비스 파일
/var/log/safefall/                      # 로그 파일
```

---

## 🔐 보안 체크리스트

- [ ] SECRET_KEY와 JWT_SECRET_KEY를 강력한 랜덤 문자열로 변경
- [ ] 기본 관리자 비밀번호 변경 (admin/admin → 새 비밀번호)
- [ ] HTTPS 설정 (Let's Encrypt)
- [ ] 방화벽 활성화 (ufw)
- [ ] SSH 키 기반 인증 사용
- [ ] 불필요한 포트 닫기
- [ ] 정기적인 보안 업데이트
- [ ] 데이터베이스 백업 자동화
- [ ] 로그 모니터링 설정

---

## 📊 모니터링

### 시스템 리소스 모니터링
```bash
# CPU, 메모리 사용량
htop

# 디스크 사용량
df -h

# 네트워크 연결
netstat -tulpn
```

### 애플리케이션 로그
```bash
# Backend 실시간 로그
sudo journalctl -u safefall-backend -f

# Nginx 접속 로그
sudo tail -f /var/log/nginx/safefall-frontend-access.log

# Nginx 에러 로그
sudo tail -f /var/log/nginx/safefall-backend-error.log
```

---

## 🔄 업데이트 방법

```bash
# 1. 코드 업데이트
cd /opt/safefallFullstack-main
git pull

# 2. Backend 업데이트
cd Back
source venv/bin/activate
pip install -r requirements.txt

# 3. Frontend 재빌드
cd ../Front
npm install
npm run build

# 4. 서비스 재시작
sudo systemctl restart safefall-backend
sudo systemctl restart nginx
```

---

## 🆘 문제 해결

### Backend가 시작되지 않을 때
```bash
# 로그 확인
sudo journalctl -u safefall-backend -n 100

# 수동 실행으로 에러 확인
cd /opt/safefallFullstack-main/Back
source venv/bin/activate
python app.py
```

### Nginx 502 Bad Gateway
```bash
# Backend 서비스 확인
sudo systemctl status safefall-backend

# Nginx 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 영상 스트리밍 문제
```bash
# videos 디렉토리 권한 확인
ls -la /opt/safefallFullstack-main/Back/videos

# 권한 수정
sudo chown -R www-data:www-data /opt/safefallFullstack-main/Back/videos
```

### 디스크 용량 부족
```bash
# 오래된 영상 파일 삭제
find /opt/safefallFullstack-main/Back/videos -type f -mtime +30 -delete

# 로그 파일 정리
sudo journalctl --vacuum-time=7d
```

---

## 💾 백업 방법

```bash
# 데이터베이스 백업
cp /opt/safefallFullstack-main/Back/instance/safefall.db \
   /backup/safefall-$(date +%Y%m%d).db

# 영상 파일 백업
tar -czf /backup/videos-$(date +%Y%m%d).tar.gz \
   /opt/safefallFullstack-main/Back/videos

# 자동 백업 스크립트 (crontab)
0 2 * * * /opt/safefallFullstack-main/backup.sh
```

---

## 📞 지원

문제가 발생하면:
1. 로그 파일 확인
2. GitHub Issues에 문제 보고
3. 시스템 상태 확인 (`systemctl status`)

---

**배포 성공을 기원합니다! 🚀**
