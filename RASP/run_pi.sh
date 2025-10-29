#!/bin/bash
# 라즈베리파이 운영 환경에서 실행

echo "🍓 Starting SafeFall client in RASPBERRY PI production mode"
echo "   Backend: http://43.203.245.90:8000"
echo "   Device: pi-01"
echo ""

export SAFEFALL_ENV=pi
python3 pi_client_improved.py