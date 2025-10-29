#!/bin/bash

echo "🔐 SafeFall 인증 포함 전체 API 테스트"
echo "======================================"
echo ""

BACKEND="http://localhost:5001"

# 사용자 입력 받기
read -p "👤 사용자 ID (기본값: 1): " USER_ID
USER_ID=${USER_ID:-1}

read -sp "🔑 비밀번호 (기본값: admin123): " PASSWORD
PASSWORD=${PASSWORD:-admin123}
echo ""
echo ""

# 1. 로그인
echo "1️⃣ 로그인 시도..."
LOGIN_RESPONSE=$(curl -s -X POST "${BACKEND}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"id\":\"${USER_ID}\",\"password\":\"${PASSWORD}\"}")

echo "$LOGIN_RESPONSE" | python3 -m json.tool
echo ""

# JWT 토큰 추출
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ 로그인 실패! 사용자 ID와 비밀번호를 확인하세요."
    exit 1
fi

echo "✅ 로그인 성공!"
echo "🎫 Access Token: ${ACCESS_TOKEN:0:50}..."
echo ""
echo ""

# 2. 대시보드 통계 (인증 필요)
echo "2️⃣ 대시보드 통계 조회"
curl -s "${BACKEND}/api/dashboard/stats" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | python3 -m json.tool
echo ""
echo ""

# 3. 사고 목록 (인증 필요)
echo "3️⃣ 사고 목록 조회"
curl -s "${BACKEND}/api/incidents/list" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | python3 -m json.tool
echo ""
echo ""

# 4. 최근 영상 목록 (인증 필요)
echo "4️⃣ 최근 영상 목록"
curl -s "${BACKEND}/api/dashboard/recent-videos" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | python3 -m json.tool
echo ""
echo ""

# 5. 사고 요약 (인증 필요)
echo "5️⃣ 사고 요약"
curl -s "${BACKEND}/api/dashboard/incidents/summary" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | python3 -m json.tool
echo ""
echo ""

# 6. 스트림 상태 (인증 불필요)
echo "6️⃣ 스트림 상태"
curl -s "${BACKEND}/api/stream/session/status" | python3 -m json.tool
echo ""
echo ""

# 7. 내 정보 조회 (인증 필요)
echo "7️⃣ 내 정보 조회"
curl -s "${BACKEND}/api/auth/me" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | python3 -m json.tool
echo ""
echo ""

echo "======================================"
echo "✅ 전체 테스트 완료!"
echo ""
echo "💡 토큰 저장됨: ACCESS_TOKEN 환경변수로 사용 가능"
echo "   예: curl -H \"Authorization: Bearer \$ACCESS_TOKEN\" ..."
echo ""
echo "📝 기본 로그인 정보:"
echo "   사용자 ID: 1"
echo "   비밀번호: admin123"
