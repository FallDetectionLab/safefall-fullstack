#!/bin/bash
# SafeFall 보안 강화 스크립트

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔒 SafeFall 보안 강화를 시작합니다..."

# 1. 방화벽 설정
echo "🔥 방화벽 설정 중..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw status
echo -e "${GREEN}✅ 방화벽 설정 완료${NC}"

# 2. fail2ban 설치 및 설정
echo "🛡️  fail2ban 설치 중..."
sudo apt install -y fail2ban

# fail2ban 설정 파일 생성
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
destemail = admin@your-domain.com
sendername = Fail2Ban
action = %(action_mwl)s

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/*error.log

[nginx-noscript]
enabled = true
port = http,https
logpath = /var/log/nginx/*access.log

[nginx-badbots]
enabled = true
port = http,https
logpath = /var/log/nginx/*access.log
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
echo -e "${GREEN}✅ fail2ban 설치 완료${NC}"

# 3. SSH 보안 강화
echo "🔐 SSH 보안 강화 중..."
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# SSH 설정 변경
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

echo -e "${YELLOW}⚠️  SSH 설정이 변경되었습니다:${NC}"
echo "   - Root 로그인 비활성화"
echo "   - 비밀번호 인증 비활성화 (SSH 키만 허용)"
echo ""
echo -e "${RED}주의: SSH 키가 설정되어 있는지 확인하세요!${NC}"
read -p "SSH를 재시작하시겠습니까? [y/N]: " restart_ssh

if [[ $restart_ssh =~ ^[Yy]$ ]]; then
    sudo systemctl restart sshd
    echo -e "${GREEN}✅ SSH 재시작 완료${NC}"
else
    echo -e "${YELLOW}⚠️  나중에 'sudo systemctl restart sshd'를 실행하세요${NC}"
fi

# 4. 자동 보안 업데이트 설정
echo "🔄 자동 보안 업데이트 설정 중..."
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
echo -e "${GREEN}✅ 자동 업데이트 설정 완료${NC}"

# 5. 시스템 업데이트
echo "📦 시스템 업데이트 중..."
sudo apt update
sudo apt upgrade -y
echo -e "${GREEN}✅ 시스템 업데이트 완료${NC}"

# 6. 파일 권한 설정
echo "📁 파일 권한 설정 중..."
PROJECT_DIR="/opt/safefallFullstack-main"

if [ -d "$PROJECT_DIR" ]; then
    # .env 파일 권한 (읽기 전용, 소유자만)
    if [ -f "$PROJECT_DIR/Back/.env" ]; then
        sudo chmod 600 "$PROJECT_DIR/Back/.env"
        echo -e "${GREEN}✅ Backend .env 권한 설정 (600)${NC}"
    fi
    
    if [ -f "$PROJECT_DIR/Front/.env" ]; then
        sudo chmod 600 "$PROJECT_DIR/Front/.env"
        echo -e "${GREEN}✅ Frontend .env 권한 설정 (600)${NC}"
    fi
    
    # videos 디렉토리
    if [ -d "$PROJECT_DIR/Back/videos" ]; then
        sudo chown -R www-data:www-data "$PROJECT_DIR/Back/videos"
        sudo chmod 750 "$PROJECT_DIR/Back/videos"
        echo -e "${GREEN}✅ videos 디렉토리 권한 설정${NC}"
    fi
    
    # instance 디렉토리 (데이터베이스)
    if [ -d "$PROJECT_DIR/Back/instance" ]; then
        sudo chown -R www-data:www-data "$PROJECT_DIR/Back/instance"
        sudo chmod 750 "$PROJECT_DIR/Back/instance"
        echo -e "${GREEN}✅ instance 디렉토리 권한 설정${NC}"
    fi
fi

# 7. Nginx 보안 헤더 추가
echo "🌐 Nginx 보안 헤더 추가 중..."
sudo tee /etc/nginx/snippets/security-headers.conf > /dev/null <<EOF
# 보안 헤더
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline' 'unsafe-eval'" always;

# Strict-Transport-Security (HTTPS 사용 시)
# add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
EOF
echo -e "${GREEN}✅ 보안 헤더 파일 생성${NC}"
echo -e "${YELLOW}⚠️  /etc/nginx/sites-available/safefall 파일에 다음 라인을 추가하세요:${NC}"
echo "   include /etc/nginx/snippets/security-headers.conf;"

# 8. 로그 로테이션 설정
echo "📋 로그 로테이션 설정 중..."
sudo tee /etc/logrotate.d/safefall > /dev/null <<EOF
/var/log/safefall/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload safefall-backend > /dev/null 2>&1 || true
    endscript
}
EOF
echo -e "${GREEN}✅ 로그 로테이션 설정 완료${NC}"

# 9. 임시 파일 정리 Cron Job 추가
echo "🗑️  자동 정리 작업 추가 중..."
(sudo crontab -l 2>/dev/null; echo "# SafeFall 자동 정리") | sudo crontab -
(sudo crontab -l 2>/dev/null; echo "0 3 * * * find $PROJECT_DIR/Back/videos -type f -mtime +30 -delete") | sudo crontab -
(sudo crontab -l 2>/dev/null; echo "0 4 * * 0 journalctl --vacuum-time=30d") | sudo crontab -
echo -e "${GREEN}✅ 자동 정리 작업 추가 완료${NC}"

# 10. 백업 스크립트 생성
echo "💾 백업 스크립트 생성 중..."
sudo tee /opt/safefallFullstack-main/backup.sh > /dev/null <<'EOF'
#!/bin/bash
# SafeFall 자동 백업 스크립트

BACKUP_DIR="/backup/safefall"
PROJECT_DIR="/opt/safefallFullstack-main"
DATE=$(date +%Y%m%d_%H%M%S)

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# 데이터베이스 백업
if [ -f "$PROJECT_DIR/Back/instance/safefall.db" ]; then
    cp "$PROJECT_DIR/Back/instance/safefall.db" "$BACKUP_DIR/db_$DATE.db"
    echo "✅ 데이터베이스 백업 완료: db_$DATE.db"
fi

# 영상 파일 백업 (최근 7일)
if [ -d "$PROJECT_DIR/Back/videos" ]; then
    tar -czf "$BACKUP_DIR/videos_$DATE.tar.gz" \
        --exclude="*.tmp" \
        -C "$PROJECT_DIR/Back" videos
    echo "✅ 영상 파일 백업 완료: videos_$DATE.tar.gz"
fi

# 설정 파일 백업
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    "$PROJECT_DIR/Back/.env" \
    "$PROJECT_DIR/Front/.env" \
    "/etc/nginx/sites-available/safefall" \
    "/etc/systemd/system/safefall-backend.service" 2>/dev/null
echo "✅ 설정 파일 백업 완료: config_$DATE.tar.gz"

# 오래된 백업 삭제 (30일 이상)
find $BACKUP_DIR -type f -mtime +30 -delete
echo "✅ 오래된 백업 파일 정리 완료"

echo "🎉 백업 완료: $BACKUP_DIR"
EOF

sudo chmod +x /opt/safefallFullstack-main/backup.sh
echo -e "${GREEN}✅ 백업 스크립트 생성 완료${NC}"

# 백업 Cron Job 추가
(sudo crontab -l 2>/dev/null; echo "0 2 * * * /opt/safefallFullstack-main/backup.sh >> /var/log/safefall/backup.log 2>&1") | sudo crontab -
echo -e "${GREEN}✅ 백업 Cron Job 추가 (매일 새벽 2시)${NC}"

# 11. 모니터링 스크립트 생성
echo "📊 모니터링 스크립트 생성 중..."
sudo tee /opt/safefallFullstack-main/monitor.sh > /dev/null <<'EOF'
#!/bin/bash
# SafeFall 시스템 모니터링

echo "=========================================="
echo "SafeFall 시스템 상태"
echo "=========================================="
echo ""

# 시스템 리소스
echo "📊 시스템 리소스:"
echo "   CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')% 사용 중"
echo "   메모리: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "   디스크: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " 사용)"}')"
echo ""

# 서비스 상태
echo "🔧 서비스 상태:"
systemctl is-active --quiet safefall-backend && echo "   ✅ Backend: Running" || echo "   ❌ Backend: Stopped"
systemctl is-active --quiet nginx && echo "   ✅ Nginx: Running" || echo "   ❌ Nginx: Stopped"
echo ""

# 디스크 사용량 경고
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️  디스크 사용량이 80%를 초과했습니다!"
fi

# 메모리 사용량 경고
MEM_USAGE=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2 * 100}')
if [ $MEM_USAGE -gt 80 ]; then
    echo "⚠️  메모리 사용량이 80%를 초과했습니다!"
fi

echo ""
echo "📝 최근 로그 (Backend):"
sudo journalctl -u safefall-backend -n 5 --no-pager
echo ""

echo "🌐 Nginx 접속 통계 (최근 1시간):"
sudo awk -v d1="$(date --date='-1 hour' '+%d/%b/%Y:%H:%M:%S')" \
    '$4 > "["d1 {print $1}' /var/log/nginx/safefall-frontend-access.log 2>/dev/null | \
    sort | uniq -c | sort -rn | head -5
echo ""
EOF

sudo chmod +x /opt/safefallFullstack-main/monitor.sh
echo -e "${GREEN}✅ 모니터링 스크립트 생성 완료${NC}"

# 12. 보안 검사 스크립트 생성
echo "🔍 보안 검사 스크립트 생성 중..."
sudo tee /opt/safefallFullstack-main/security-check.sh > /dev/null <<'EOF'
#!/bin/bash
# SafeFall 보안 검사

echo "🔐 SafeFall 보안 검사 시작..."
echo ""

ISSUES=0

# 1. .env 파일 권한 확인
echo "1️⃣  환경 변수 파일 권한 확인:"
if [ -f "/opt/safefallFullstack-main/Back/.env" ]; then
    PERM=$(stat -c %a "/opt/safefallFullstack-main/Back/.env")
    if [ "$PERM" == "600" ] || [ "$PERM" == "400" ]; then
        echo "   ✅ Backend .env: OK ($PERM)"
    else
        echo "   ❌ Backend .env: 위험! 현재 권한: $PERM (권장: 600)"
        ((ISSUES++))
    fi
fi

# 2. 기본 비밀번호 사용 확인
echo ""
echo "2️⃣  기본 비밀번호 사용 확인:"
if grep -q "your-secret-key-change-this" "/opt/safefallFullstack-main/Back/.env" 2>/dev/null; then
    echo "   ❌ 기본 SECRET_KEY를 사용 중입니다!"
    ((ISSUES++))
else
    echo "   ✅ SECRET_KEY: OK"
fi

if grep -q "your-jwt-secret-key-change-this" "/opt/safefallFullstack-main/Back/.env" 2>/dev/null; then
    echo "   ❌ 기본 JWT_SECRET_KEY를 사용 중입니다!"
    ((ISSUES++))
else
    echo "   ✅ JWT_SECRET_KEY: OK"
fi

# 3. 방화벽 상태 확인
echo ""
echo "3️⃣  방화벽 상태:"
if sudo ufw status | grep -q "Status: active"; then
    echo "   ✅ UFW 방화벽 활성화됨"
else
    echo "   ❌ UFW 방화벽이 비활성화되어 있습니다!"
    ((ISSUES++))
fi

# 4. fail2ban 상태 확인
echo ""
echo "4️⃣  fail2ban 상태:"
if systemctl is-active --quiet fail2ban; then
    echo "   ✅ fail2ban 실행 중"
    BANNED=$(sudo fail2ban-client status sshd 2>/dev/null | grep "Currently banned" | awk '{print $4}')
    echo "   📊 현재 차단된 IP: $BANNED"
else
    echo "   ❌ fail2ban이 실행되지 않습니다!"
    ((ISSUES++))
fi

# 5. SSL 인증서 확인
echo ""
echo "5️⃣  SSL 인증서 확인:"
if [ -d "/etc/letsencrypt/live" ]; then
    echo "   ✅ SSL 인증서 발견"
    # 만료 날짜 확인
    for cert in /etc/letsencrypt/live/*/cert.pem; do
        if [ -f "$cert" ]; then
            DOMAIN=$(basename $(dirname $cert))
            EXPIRY=$(sudo openssl x509 -enddate -noout -in "$cert" | cut -d= -f2)
            echo "   📅 $DOMAIN: 만료일 $EXPIRY"
        fi
    done
else
    echo "   ⚠️  SSL 인증서가 설치되지 않았습니다 (HTTPS 미사용)"
fi

# 6. 디스크 공간 확인
echo ""
echo "6️⃣  디스크 공간 확인:"
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo "   ✅ 디스크 사용량: ${DISK_USAGE}%"
else
    echo "   ❌ 디스크 사용량이 높습니다: ${DISK_USAGE}%"
    ((ISSUES++))
fi

# 7. SSH 설정 확인
echo ""
echo "7️⃣  SSH 보안 설정:"
if sudo grep -q "^PermitRootLogin no" /etc/ssh/sshd_config; then
    echo "   ✅ Root 로그인 비활성화됨"
else
    echo "   ❌ Root 로그인이 허용되어 있습니다!"
    ((ISSUES++))
fi

if sudo grep -q "^PasswordAuthentication no" /etc/ssh/sshd_config; then
    echo "   ✅ 비밀번호 인증 비활성화됨"
else
    echo "   ⚠️  비밀번호 인증이 활성화되어 있습니다"
fi

# 결과 요약
echo ""
echo "=========================================="
if [ $ISSUES -eq 0 ]; then
    echo "✅ 보안 검사 완료: 문제 없음"
else
    echo "❌ 보안 검사 완료: $ISSUES개의 문제 발견"
    echo "   위의 문제들을 해결하세요!"
fi
echo "=========================================="

exit $ISSUES
EOF

sudo chmod +x /opt/safefallFullstack-main/security-check.sh
echo -e "${GREEN}✅ 보안 검사 스크립트 생성 완료${NC}"

# 완료 메시지
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 보안 강화 완료!${NC}"
echo "=========================================="
echo ""
echo "📝 생성된 파일:"
echo "   /opt/safefallFullstack-main/backup.sh          - 백업 스크립트"
echo "   /opt/safefallFullstack-main/monitor.sh         - 모니터링 스크립트"
echo "   /opt/safefallFullstack-main/security-check.sh  - 보안 검사 스크립트"
echo ""
echo "🔧 유용한 명령어:"
echo "   보안 검사:     sudo /opt/safefallFullstack-main/security-check.sh"
echo "   시스템 모니터: sudo /opt/safefallFullstack-main/monitor.sh"
echo "   수동 백업:     sudo /opt/safefallFullstack-main/backup.sh"
echo ""
echo "⚠️  중요 확인사항:"
echo "   1. SSH 키가 설정되어 있는지 확인 (비밀번호 인증 비활성화)"
echo "   2. .env 파일의 SECRET_KEY 변경"
echo "   3. 기본 관리자 비밀번호 변경 (admin/admin)"
echo "   4. Nginx 설정에 보안 헤더 추가"
echo ""
