#!/bin/bash

echo "🍎 SafeFall 로컬 맥북 실행 스크립트"
echo "=================================="

# 현재 디렉토리 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 백엔드 실행 함수
start_backend() {
    echo "🔧 백엔드 서버 시작 중... (포트: 5001)"
    cd Back
    
    # 가상환경 활성화
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "⚠️  가상환경이 없습니다. 먼저 설치해주세요:"
        echo "   cd Back && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
    
    # Flask 앱 실행
    python app.py &
    BACKEND_PID=$!
    echo "✅ 백엔드 PID: $BACKEND_PID"
    cd ..
}

# 프론트엔드 실행 함수
start_frontend() {
    echo "🎨 프론트엔드 서버 시작 중..."
    cd Front
    
    # node_modules 확인
    if [ ! -d "node_modules" ]; then
        echo "⚠️  node_modules가 없습니다. 먼저 설치해주세요:"
        echo "   cd Front && npm install"
        exit 1
    fi
    
    # Vite 개발 서버 실행
    npm run dev &
    FRONTEND_PID=$!
    echo "✅ 프론트엔드 PID: $FRONTEND_PID"
    cd ..
}

# 종료 핸들러
cleanup() {
    echo ""
    echo "🛑 서버 종료 중..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "   백엔드 종료됨"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "   프론트엔드 종료됨"
    fi
    exit 0
}

trap cleanup INT TERM

# 메인 실행
echo ""
start_backend
sleep 3
start_frontend

echo ""
echo "=================================="
echo "✅ SafeFall 시스템 실행 완료!"
echo ""
echo "📍 백엔드:      http://localhost:5001"
echo "📍 프론트엔드:  http://localhost:5173"
echo "📍 Health Check: http://localhost:5001/health"
echo ""
echo "종료하려면 Ctrl+C를 누르세요"
echo "=================================="

# 백그라운드 프로세스 대기
wait
