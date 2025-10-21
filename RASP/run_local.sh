#!/bin/bash
# 로컬 개발 환경에서 실행

echo "🖥️ Starting SafeFall client in LOCAL development mode"
echo "   Backend: http://localhost:5000"
echo "   Device: local-dev"
echo ""

export SAFEFALL_ENV=local
python3 pi_client_improved.py