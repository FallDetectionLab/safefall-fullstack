#!/bin/bash

# SafeFall 빠른 배포 스크립트

echo "🚀 SafeFall 배포를 시작합니다..."

# 1. 환경 변수 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하여 .env를 만들어주세요."
    cp .env.example .env
    echo "✅ .env 파일이 생성되었습니다. 파일을 수정한 후 다시 실행해주세요."
    exit 1
fi

# 2. Frontend 환경 변수 확인
if [ ! -f Front/.env ]; then
    echo "⚠️  Front/.env 파일이 없습니다."
    read -p "Backend 서버 주소를 입력하세요 (예: http://your-server-ip:5000): " backend_url
    echo "VITE_BACKEND_URL=$backend_url" > Front/.env
    echo "✅ Front/.env 파일이 생성되었습니다."
fi

# 3. Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되어 있지 않습니다."
    echo "Docker를 설치한 후 다시 시도해주세요: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi

# 4. 이전 컨테이너 정리
echo "🧹 이전 컨테이너를 정리합니다..."
docker-compose down

# 5. 이미지 빌드
echo "🔨 Docker 이미지를 빌드합니다..."
docker-compose build

# 6. 컨테이너 실행
echo "▶️  컨테이너를 실행합니다..."
docker-compose up -d

# 7. 상태 확인
echo "✅ 배포가 완료되었습니다!"
echo ""
echo "📊 컨테이너 상태:"
docker-compose ps

echo ""
echo "🌐 접속 정보:"
echo "   Frontend: http://localhost"
echo "   Backend:  http://localhost:5000"
echo ""
echo "📝 로그 확인: docker-compose logs -f"
echo "🛑 중지: docker-compose down"
