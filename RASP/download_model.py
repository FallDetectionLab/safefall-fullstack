#!/usr/bin/env python3
"""YOLO11 모델 다운로드 스크립트"""

import os
from pathlib import Path

try:
    from ultralytics import YOLO
    
    # models 디렉토리 생성
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)
    
    print("🤖 YOLO11n 모델 다운로드 중...")
    
    # YOLO 객체 생성 시 자동 다운로드
    model = YOLO('yolo11n.pt')
    
    # 다운로드된 파일 확인 및 이동
    current_file = Path('yolo11n.pt')
    target_file = models_dir / 'yolo11n.pt'
    
    if current_file.exists() and not target_file.exists():
        current_file.rename(target_file)
        print(f"✅ 모델 저장: {target_file}")
    elif target_file.exists():
        print(f"✅ 모델 이미 존재: {target_file}")
    
    # 모델 정보 출력
    print(f"\n📊 모델 정보:")
    print(f"   경로: {target_file}")
    print(f"   크기: {target_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    print("\n🎉 다운로드 완료!")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    print("\n대안: 수동 다운로드")
    print("1. https://github.com/ultralytics/assets 방문")
    print("2. Releases에서 yolo11n.pt 찾기")
    print("3. models/ 폴더에 저장")

