#!/bin/bash

echo "🔍 SafeFall 데이터베이스 확인"
echo "=================================="
echo ""

DB_PATH="/Users/choihyunjin/poly/safefall-local/Back/instance/safefall.db"

echo "📊 incidents 테이블 조회..."
echo ""

# 모든 사고 확인
echo "전체 사고 목록:"
sqlite3 "$DB_PATH" "SELECT id, incident_type, detected_at, is_checked, confidence FROM incidents ORDER BY detected_at DESC LIMIT 10;"

echo ""
echo "=================================="
echo ""

# 미확인 사고만
echo "⚠️ 미확인 사고 (is_checked = 0):"
sqlite3 "$DB_PATH" "SELECT id, incident_type, detected_at, confidence FROM incidents WHERE is_checked = 0 ORDER BY detected_at DESC;"

echo ""
echo "=================================="
echo ""

# 통계
echo "📈 통계:"
echo -n "  전체 사고: "
sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM incidents;"
echo -n "  미확인: "
sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM incidents WHERE is_checked = 0;"
echo -n "  확인됨: "
sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM incidents WHERE is_checked = 1;"

echo ""
echo "=================================="
echo ""

echo "🗑️ 미확인 사고를 모두 확인 처리하려면:"
echo "   sqlite3 '$DB_PATH' \"UPDATE incidents SET is_checked = 1;\""
echo ""
echo "🗑️ 모든 사고를 삭제하려면:"
echo "   sqlite3 '$DB_PATH' \"DELETE FROM incidents;\""
