#!/bin/bash
# SafeFall 서버 배포 스크립트

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 SafeFall 서버 배포를 시작합니다..."

# 설정 변수
PROJECT_DIR="/opt/safefallFullstack-main"
BACKEND_DIR="$PROJECT_DIR/Back"
FRONTEND_DIR="$PROJECT_DIR/Front"
LOGS_DIR="/var/log/safefall"
USER="www-data"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수: 에러 출력
error() {
    echo -e "${RED}❌ 에러: $1${NC}"
    exit 1
}

# 함수: 성공 출력
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 함수: 경고 출력
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. 시스템 패키지 업데이트
echo "📦 시스템 패키지 업데이트..."
sudo apt update || error "apt update 실패"

# 2. 필수 패키지 설치
echo "📦 필수 패키지 설치..."
sudo apt install -y python3-pip python3-venv nginx git curl || error "패키지 설치 실패"

# 3. Node.js 설치 (없는 경우)
if ! command -v node &> /dev/null; then
    echo "📦 Node.js 설치 중..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs || error "Node.js 설치 실패"
    success "Node.js 설치 완료"
else
    success "Node.js 이미 설치됨: $(node -v)"
fi

# 4. 프로젝트 디렉토리 생성
echo "📁 프로젝트 디렉토리 생성..."
sudo mkdir -p $PROJECT_DIR
sudo chown -R $USER:$USER $PROJECT_DIR

# 5. 로그 디렉토리 생성
echo "📁 로그 디렉토리 생성..."
sudo mkdir -p $LOGS_DIR
sudo chown -R $USER:$USER $LOGS_DIR

# 6. Backend 설정
echo "🐍 Backend 설정 중..."
cd $BACKEND_DIR

# 가상환경 생성
if [ ! -d "venv" ]; then
    python3 -m venv venv || error "가상환경 생성 실패"
    success "가상환경 생성 완료"
fi

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt || error "Python 패키지 설치 실패"
pip install gunicorn || error "Gunicorn 설치 실패"
success "Backend 의존성 설치 완료"

# .env 파일 확인
if [ ! -f ".env" ]; then
    warning ".env 파일이 없습니다. .env.production을 복사합니다."
    cp .env.production .env
    warning "⚠️  .env 파일을 수정하여 SECRET_KEY와 JWT_SECRET_KEY를 변경하세요!"
    read -p "계속하려면 Enter를 누르세요..."
fi

# 데이터베이스 초기화
echo "💾 데이터베이스 초기화..."
python init_default_user.py || warning "데이터베이스 초기화 실패 (이미 존재할 수 있음)"

# 필요한 디렉토리 생성
mkdir -p instance videos static
success "Backend 설정 완료"

# 7. Frontend 빌드
echo "⚛️  Frontend 빌드 중..."
cd $FRONTEND_DIR

# .env 파일 확인
if [ ! -f ".env" ]; then
    warning ".env 파일이 없습니다."
    read -p "Backend URL을 입력하세요 (예: https://api.your-domain.com): " backend_url
    echo "VITE_BACKEND_URL=$backend_url" > .env
    echo "VITE_ENV=production" >> .env
    success ".env 파일 생성 완료"
fi

# 의존성 설치
npm install || error "npm install 실패"

# 프로덕션 빌드
npm run build || error "빌드 실패"
success "Frontend 빌드 완료"

# 8. Systemd 서비스 설정
echo "⚙️  Systemd 서비스 설정..."
sudo cp $PROJECT_DIR/safefall-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable safefall-backend
success "Systemd 서비스 설정 완료"

# 9. Nginx 설정
echo "🌐 Nginx 설정..."
sudo cp $PROJECT_DIR/nginx-production.conf /etc/nginx/sites-available/safefall

# 도메인 입력 받기
read -p "도메인 이름을 입력하세요 (예: your-domain.com, 없으면 Enter): " domain_name

if [ -n "$domain_name" ]; then
    # nginx 설정 파일에서 도메인 변경
    sudo sed -i "s/your-domain.com/$domain_name/g" /etc/nginx/sites-available/safefall
    sudo sed -i "s/api.your-domain.com/api.$domain_name/g" /etc/nginx/sites-available/safefall
    success "도메인 설정: $domain_name"
fi

# 심볼릭 링크 생성
if [ ! -L /etc/nginx/sites-enabled/safefall ]; then
    sudo ln -s /etc/nginx/sites-available/safefall /etc/nginx/sites-enabled/
fi

# Nginx 설정 테스트
sudo nginx -t || error "Nginx 설정 오류"

# 10. 방화벽 설정
echo "🔥 방화벽 설정..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 22/tcp
    success "방화벽 규칙 추가"
fi

# 11. SSL 인증서 설치 (선택)
echo ""
read -p "SSL 인증서를 설치하시겠습니까? (Let's Encrypt) [y/N]: " install_ssl

if [[ $install_ssl =~ ^[Yy]$ ]]; then
    if [ -z "$domain_name" ]; then
        warning "도메인 이름이 필요합니다. SSL 인증서 설치를 건너뜁니다."
    else
        sudo apt install -y certbot python3-certbot-nginx
        sudo certbot --nginx -d $domain_name -d api.$domain_name || warning "SSL 인증서 설치 실패"
        success "SSL 인증서 설치 완료"
    fi
fi

# 12. 서비스 시작
echo "🚀 서비스 시작..."
sudo systemctl start safefall-backend || error "Backend 서비스 시작 실패"
sudo systemctl restart nginx || error "Nginx 재시작 실패"

# 13. 상태 확인
echo ""
echo "📊 서비스 상태:"
sudo systemctl status safefall-backend --no-pager
echo ""
sudo systemctl status nginx --no-pager

# 14. 완료 메시지
echo ""
echo "=========================================="
success "🎉 배포 완료!"
echo "=========================================="
echo ""
echo "📍 접속 정보:"
if [ -n "$domain_name" ]; then
    echo "   Frontend: https://$domain_name"
    echo "   Backend:  https://api.$domain_name"
else
    echo "   Frontend: http://$(hostname -I | awk '{print $1}')"
    echo "   Backend:  http://$(hostname -I | awk '{print $1}'):5000"
fi
echo ""
echo "📝 유용한 명령어:"
echo "   서비스 상태 확인:  sudo systemctl status safefall-backend"
echo "   서비스 재시작:     sudo systemctl restart safefall-backend"
echo "   로그 확인:         sudo journalctl -u safefall-backend -f"
echo "   Nginx 로그:        sudo tail -f /var/log/nginx/safefall-*.log"
echo ""
echo "⚠️  중요:"
echo "   1. $BACKEND_DIR/.env 파일에서 SECRET_KEY를 변경하세요"
echo "   2. 기본 관리자 계정: admin / admin (변경 필요!)"
echo "   3. 정기적으로 백업을 수행하세요"
echo ""
