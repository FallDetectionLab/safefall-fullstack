#!/bin/bash

echo "🔧 SafeFall 백엔드 단독 실행"
echo "=================================="

cd "$(dirname "$0")/Back"

# 가상환경 확인
if [ ! -d "venv" ]; then
    echo "❌ 가상환경이 없습니다!"
    echo "   다음 명령어로 설치하세요:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# 가상환경 활성화
echo "✅ 가상환경 활성화..."
source venv/bin/activate

# 환경변수 확인
echo "📋 환경 설정:"
echo "   FLASK_ENV: ${FLASK_ENV:-development}"
echo "   DEBUG: ${DEBUG:-True}"
echo ""

# Flask 실행
echo "🚀 Flask 서버 시작..."
echo "   포트: 5001"
echo "   주소: http://localhost:5001"
echo ""
echo "⚠️  '📋 등록된 라우트 목록:' 부분을 주의깊게 확인하세요!"
echo "=================================="
echo ""

python app.py
