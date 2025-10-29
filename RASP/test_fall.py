#!/usr/bin/env python3
"""
낙상 감지 테스트 스크립트
실제 사고가 없어도 백엔드에 낙상 신호를 보내서 테스트
"""
import requests
import json
from datetime import datetime, timezone

# 백엔드 URL
BACKEND_URL = "http://192.168.102.41:5001"

def test_fall_detection():
    """낙상 감지 테스트"""
    
    print("🧪 낙상 감지 테스트 시작...")
    print(f"   Backend: {BACKEND_URL}")
    print()
    
    # 테스트 데이터
    incident_data = {
        "device_id": "pi-01",
        "incident_type": "fall",
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.95,
        "user_id": "1"
    }
    
    print("📤 낙상 신호 전송 중...")
    print(f"   타입: {incident_data['incident_type']}")
    print(f"   신뢰도: {incident_data['confidence']}")
    print(f"   시간: {incident_data['detected_at']}")
    print()
    
    try:
        # POST 요청
        response = requests.post(
            f"{BACKEND_URL}/api/incidents/report",
            json=incident_data,
            timeout=10
        )
        
        print(f"📥 응답 수신: HTTP {response.status_code}")
        print()
        
        if response.status_code == 201:
            result = response.json()
            print("✅ 낙상 신호 전송 성공!")
            print()
            print("📋 저장된 사고 정보:")
            incident = result.get('incident', {})
            print(f"   ID: {incident.get('id')}")
            print(f"   타입: {incident.get('incident_type')}")
            print(f"   영상 파일: {incident.get('video_path')}")
            print(f"   썸네일: {incident.get('thumbnail_path')}")
            print(f"   길이: {incident.get('duration')}초")
            print()
            print("🎉 이제 프론트엔드에서 알림이 뜰 거예요!")
            print(f"🎬 영상 URL: {BACKEND_URL}/api/incidents/{incident.get('id')}/video")
            
        else:
            print(f"❌ 전송 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 연결 실패: {BACKEND_URL}에 연결할 수 없습니다")
        print("   백엔드가 실행 중인지 확인하세요!")
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    test_fall_detection()
