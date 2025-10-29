#!/bin/bash

echo "🔧 SafeFall 초기 설정 스크립트"
echo "======================================"
echo ""

cd "$(dirname "$0")/Back"

# 가상환경 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ 가상환경이 없습니다!"
    exit 1
fi

echo "1️⃣ 기본 사용자 생성..."
python init_default_user.py

echo ""
echo "======================================"
echo "✅ 초기 설정 완료!"
echo ""
echo "📝 로그인 정보:"
echo "   사용자명: Administrator"
echo "   비밀번호: admin123"
echo ""
echo "🔐 보안 경고:"
echo "   운영 환경에서는 반드시 비밀번호를 변경하세요!"
echo ""
echo "🚀 이제 다음 명령어로 테스트할 수 있습니다:"
echo "   cd .."
echo "   chmod +x test_api_with_auth.sh"
echo "   ./test_api_with_auth.sh"
echo "======================================"
