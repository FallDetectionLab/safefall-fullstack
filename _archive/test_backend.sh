#!/bin/bash

echo "🔍 SafeFall 백엔드 디버깅 스크립트"
echo "=================================="
echo ""

# 백엔드 URL
BACKEND_URL="http://localhost:5001"

# 1. Health Check
echo "1️⃣ Health Check 테스트..."
curl -s "${BACKEND_URL}/health" | python3 -m json.tool
echo ""
echo ""

# 2. 등록된 라우트 확인
echo "2️⃣ 백엔드 로그 확인 (등록된 라우트 목록)"
echo "   → 백엔드 터미널에서 '📋 등록된 라우트 목록:' 부분을 확인하세요"
echo ""
echo ""

# 3. API 엔드포인트 테스트
echo "3️⃣ API 엔드포인트 테스트..."
echo ""

echo "   [Auth] POST /api/auth/login"
curl -s -X POST "${BACKEND_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"wrong"}' | python3 -m json.tool
echo ""
echo ""

echo "   [Stream] GET /api/stream/status"
curl -s "${BACKEND_URL}/api/stream/status" | python3 -m json.tool
echo ""
echo ""

echo "   [Dashboard] GET /api/dashboard/stats"
curl -s "${BACKEND_URL}/api/dashboard/stats" | python3 -m json.tool
echo ""
echo ""

echo "=================================="
echo "✅ 테스트 완료!"
echo ""
echo "💡 만약 404 에러가 나온다면:"
echo "   1. 백엔드 터미널에서 '📋 등록된 라우트 목록' 확인"
echo "   2. Blueprint 등록 오류 메시지 확인"
echo "   3. Python 모듈 import 오류 확인"
