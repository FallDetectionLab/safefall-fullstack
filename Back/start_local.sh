#!/bin/bash
# SafeFall 백엔드 로컬 실행 스크립트

cd "$(dirname "$0")"

echo "🚀 SafeFall 백엔드를 시작합니다..."
echo ""

# 가상환경 확인
if [ ! -d "venv" ]; then
    echo "📦 가상환경을 생성합니다..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔌 가상환경을 활성화합니다..."
source venv/bin/activate

# 의존성 설치 확인
if [ ! -f "venv/.dependencies_installed" ]; then
    echo "📦 의존성을 설치합니다..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/.dependencies_installed
fi

# 필요한 디렉토리 생성
mkdir -p instance videos static .cache/torch

echo ""
echo "✅ 백엔드 서버를 시작합니다..."
echo "📍 URL: http://localhost:5000"
echo "📍 Health Check: http://localhost:5000/health"
echo ""
echo "⏹️  종료하려면 Ctrl+C를 누르세요"
echo ""

python app.py
