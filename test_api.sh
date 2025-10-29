#!/bin/bash

echo "🧪 SafeFall API 테스트 스크립트"
echo "=================================="
echo ""

BACKEND="http://localhost:5001"

# 1. Health Check (GET)
echo "1️⃣ Health Check"
curl -s "${BACKEND}/health" | python3 -m json.tool
echo ""
echo ""

# 2. 로그인 테스트 (POST)
echo "2️⃣ 로그인 테스트 (잘못된 비밀번호)"
curl -s -X POST "${BACKEND}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "wrongpassword"
  }' | python3 -m json.tool
echo ""
echo ""

# 3. 로그인 성공 테스트 (올바른 비밀번호로 변경 필요)
echo "3️⃣ 로그인 테스트 (올바른 비밀번호 - 직접 입력 필요)"
echo "   → 다음 명령어를 직접 실행하세요:"
echo '   curl -X POST http://localhost:5001/api/auth/login \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"username":"admin","password":"YOUR_PASSWORD"}'"'"
echo ""
echo ""

# 4. Stream Status (GET)
echo "4️⃣ 스트리밍 상태 확인"
curl -s "${BACKEND}/api/stream/session/status" | python3 -m json.tool
echo ""
echo ""

# 5. Dashboard Stats (GET)
echo "5️⃣ 대시보드 통계"
curl -s "${BACKEND}/api/dashboard/stats" | python3 -m json.tool
echo ""
echo ""

# 6. Incidents List (GET)
echo "6️⃣ 사고 목록"
curl -s "${BACKEND}/api/incidents/list" | python3 -m json.tool
echo ""
echo ""

echo "=================================="
echo "✅ 테스트 완료!"
echo ""
echo "💡 참고:"
echo "   - GET 요청: 브라우저 주소창에서도 가능"
echo "   - POST 요청: curl, Postman, 프론트엔드에서만 가능"
echo ""
echo "📍 테스트 가능한 GET 엔드포인트:"
echo "   http://localhost:5001/health"
echo "   http://localhost:5001/api/stream/session/status"
echo "   http://localhost:5001/api/dashboard/stats"
echo "   http://localhost:5001/api/incidents/list"
