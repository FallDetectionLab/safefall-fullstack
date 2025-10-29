#!/bin/bash
# SafeFall 프론트엔드 로컬 실행 스크립트

cd "$(dirname "$0")"

echo "🚀 SafeFall 프론트엔드를 시작합니다..."
echo ""

# node_modules 확인
if [ ! -d "node_modules" ]; then
    echo "📦 의존성을 설치합니다..."
    npm install
fi

echo ""
echo "✅ 프론트엔드 개발 서버를 시작합니다..."
echo "📍 URL: http://localhost:5173"
echo ""
echo "⏹️  종료하려면 Ctrl+C를 누르세요"
echo ""

npm run dev
