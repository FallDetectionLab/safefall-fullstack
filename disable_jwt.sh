#!/bin/bash

echo "🔓 JWT 인증 비활성화 중..."
echo "=================================="
echo ""

cd "$(dirname "$0")/Back"

# 백업 생성
echo "1️⃣ 백업 생성..."
mkdir -p _auth_backup
cp api/dashboard.py _auth_backup/
cp api/incidents.py _auth_backup/
echo "   ✅ 백업 완료: Back/_auth_backup/"
echo ""

# dashboard.py 수정
echo "2️⃣ dashboard.py 인증 제거..."
sed -i '' 's/@jwt_required()/# @jwt_required()  # 🔓 개발용: 인증 비활성화/g' api/dashboard.py
sed -i '' 's/current_user_id = get_jwt_identity()/# current_user_id = get_jwt_identity()  # 🔓 개발용: 인증 비활성화\n    current_user_id = "1"  # 기본 사용자 ID/g' api/dashboard.py
echo "   ✅ 완료"
echo ""

# incidents.py 수정
echo "3️⃣ incidents.py 인증 제거..."
sed -i '' 's/@jwt_required()/# @jwt_required()  # 🔓 개발용: 인증 비활성화/g' api/incidents.py
sed -i '' 's/current_user_id = get_jwt_identity()/# current_user_id = get_jwt_identity()  # 🔓 개발용: 인증 비활성화\n    current_user_id = "1"  # 기본 사용자 ID/g' api/incidents.py
echo "   ✅ 완료"
echo ""

echo "=================================="
echo "✅ JWT 인증 비활성화 완료!"
echo ""
echo "📝 변경사항:"
echo "   - @jwt_required() → 주석 처리"
echo "   - get_jwt_identity() → 기본 사용자 '1' 사용"
echo ""
echo "🔒 나중에 다시 활성화하려면:"
echo "   - _auth_backup/ 폴더의 파일 복원"
echo "   - 또는 주석 제거"
echo ""
echo "🔄 백엔드를 재시작하세요:"
echo "   cd .. && ./restart_backend.sh"
