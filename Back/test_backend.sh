#!/bin/bash
# 백엔드 API 테스트 스크립트

BASE_URL="http://localhost:5000"

echo "🧪 SafeFall 백엔드 테스트"
echo "=========================="

# 1. 헬스체크
echo -e "\n1️⃣ 헬스체크"
curl -s "$BASE_URL/health" | jq .

# 2. 회원가입
echo -e "\n2️⃣ 회원가입"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "test1234"
  }')

echo $REGISTER_RESPONSE | jq .

# 3. 로그인
echo -e "\n3️⃣ 로그인"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test1234"
  }')

echo $LOGIN_RESPONSE | jq .

# 토큰 추출
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Token: $ACCESS_TOKEN"

# 4. 스트리밍 세션 시작
echo -e "\n4️⃣ 스트리밍 세션 시작"
curl -s -X POST "$BASE_URL/api/stream/session/start" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "pi-test"}' | jq .

# 5. 세션 상태 확인
echo -e "\n5️⃣ 세션 상태"
curl -s "$BASE_URL/api/stream/session/status" | jq .

# 6. 버퍼 상태
echo -e "\n6️⃣ 버퍼 상태"
curl -s "$BASE_URL/api/stream/buffer/status" | jq .

# 7. 사고 신호 전송 (테스트)
echo -e "\n7️⃣ 사고 신호 전송"
curl -s -X POST "$BASE_URL/api/incidents/report" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "pi-test",
    "incident_type": "fall",
    "confidence": 0.95,
    "user_id": 1
  }' | jq .

# 8. 사고 목록 조회
echo -e "\n8️⃣ 사고 목록 조회"
curl -s -X GET "$BASE_URL/api/incidents/list" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

# 9. 통계 조회
echo -e "\n9️⃣ 통계"
curl -s -X GET "$BASE_URL/api/incidents/stats" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

# 10. 세션 종료
echo -e "\n🔟 스트리밍 세션 종료"
curl -s -X POST "$BASE_URL/api/stream/session/stop" | jq .

echo -e "\n✅ 테스트 완료!"