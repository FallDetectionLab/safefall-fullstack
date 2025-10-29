#!/bin/bash

echo "🔄 SafeFall 백엔드 재시작"
echo "=================================="

# 5001 포트 사용 중인 프로세스 종료
echo "1️⃣ 기존 백엔드 프로세스 종료 중..."
PID=$(lsof -ti:5001)
if [ ! -z "$PID" ]; then
    kill -9 $PID
    echo "   ✅ PID $PID 종료됨"
else
    echo "   ℹ️  실행 중인 프로세스 없음"
fi

sleep 1

# 백엔드 디렉토리로 이동
cd "$(dirname "$0")/Back"

# 가상환경 활성화
if [ ! -d "venv" ]; then
    echo "❌ 가상환경이 없습니다!"
    exit 1
fi

source venv/bin/activate

# Flask 실행
echo ""
echo "2️⃣ 백엔드 재시작 중..."
echo "=================================="
python app.py
