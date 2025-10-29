#!/usr/bin/env python3
"""
SafeFall 통합 테스트 스크립트
라즈베리파이 없이 로컬에서 전체 흐름 테스트
"""

import os
import sys
import time
import requests
import cv2
import numpy as np
from datetime import datetime

# 설정
BACKEND_URL = "http://localhost:5000"
DEVICE_ID = "test-device"


def create_test_frame():
    """테스트용 더미 프레임 생성"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 배경 그라데이션
    for y in range(480):
        color_val = int(50 + 100 * (y / 480))
        frame[y, :] = [color_val, color_val // 2, color_val // 3]
    
    # 텍스트
    cv2.putText(frame, "SafeFall Test Frame", (150, 200), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (180, 250), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # 랜덤 도형
    cv2.circle(frame, (320, 350), 50, (0, 255, 0), -1)
    
    return frame


def test_backend_connection():
    """백엔드 연결 테스트"""
    print("\n" + "=" * 60)
    print("1️⃣  백엔드 연결 테스트")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 백엔드 연결 성공!")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Checks: {data.get('checks')}")
            return True
        else:
            print(f"❌ 백엔드 응답 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 백엔드 연결 실패: {e}")
        print("\n💡 백엔드 서버를 먼저 실행하세요:")
        print("   cd Back")
        print("   python app.py")
        return False


def test_stream_session():
    """스트리밍 세션 시작 테스트"""
    print("\n" + "=" * 60)
    print("2️⃣  스트리밍 세션 시작 테스트")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/stream/session/start",
            json={'device_id': DEVICE_ID},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 세션 시작 성공!")
            print(f"   Session ID: {data['session']['id']}")
            print(f"   Device ID: {data['session']['device_id']}")
            return True
        else:
            print(f"❌ 세션 시작 실패: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 세션 시작 오류: {e}")
        return False


def test_frame_upload():
    """프레임 업로드 테스트"""
    print("\n" + "=" * 60)
    print("3️⃣  프레임 업로드 테스트 (30개 프레임)")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for i in range(30):
        try:
            # 테스트 프레임 생성
            frame = create_test_frame()
            
            # JPEG 인코딩
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()
            
            # 업로드
            files = {'frame': ('frame.jpg', frame_bytes, 'image/jpeg')}
            data = {'device_id': DEVICE_ID}
            
            response = requests.post(
                f"{BACKEND_URL}/api/stream/upload",
                files=files,
                data=data,
                timeout=2
            )
            
            if response.status_code == 200:
                success_count += 1
                if (i + 1) % 10 == 0:
                    print(f"   ✅ {i + 1}개 프레임 업로드 완료")
            else:
                fail_count += 1
                print(f"   ❌ 프레임 {i + 1} 업로드 실패: {response.status_code}")
            
            time.sleep(0.033)  # ~30fps
            
        except Exception as e:
            fail_count += 1
            print(f"   ❌ 프레임 {i + 1} 오류: {e}")
    
    print(f"\n📊 업로드 결과: 성공 {success_count}개, 실패 {fail_count}개")
    return success_count > 0


def test_incident_report():
    """낙상 사고 신고 테스트"""
    print("\n" + "=" * 60)
    print("4️⃣  낙상 사고 신고 테스트")
    print("=" * 60)
    
    try:
        incident_data = {
            'device_id': DEVICE_ID,
            'incident_type': 'fall',
            'detected_at': datetime.utcnow().isoformat() + 'Z',
            'confidence': 0.95,
            'user_id': 'admin'
        }
        
        print(f"📤 사고 데이터 전송 중...")
        print(f"   타입: {incident_data['incident_type']}")
        print(f"   신뢰도: {incident_data['confidence']}")
        
        response = requests.post(
            f"{BACKEND_URL}/api/incidents/report",
            json=incident_data,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ 사고 신고 성공!")
            print(f"   Incident ID: {data['incident']['id']}")
            print(f"   Video Path: {data['incident']['video_path']}")
            print(f"   Duration: {data['incident']['duration']}초")
            return data['incident']['id']
        else:
            print(f"❌ 사고 신고 실패: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 사고 신고 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_incident_list(incident_id):
    """사고 목록 조회 테스트"""
    print("\n" + "=" * 60)
    print("5️⃣  사고 목록 조회 테스트")
    print("=" * 60)
    
    # 먼저 로그인 필요 (토큰 획득)
    try:
        # 로그인
        login_response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={'id': 'admin', 'password': 'admin123'},
            timeout=5
        )
        
        if login_response.status_code != 200:
            print(f"⚠️  로그인 실패. 기본 사용자가 생성되지 않았을 수 있습니다.")
            print(f"💡 다음 명령어를 실행하세요:")
            print(f"   cd Back")
            print(f"   python init_default_user.py")
            return False
        
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 사고 목록 조회
        response = requests.get(
            f"{BACKEND_URL}/api/incidents/list",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 사고 목록 조회 성공!")
            print(f"   전체 사고 수: {data['total']}")
            print(f"   현재 페이지 사고 수: {len(data['incidents'])}")
            
            if data['incidents']:
                print(f"\n📋 최근 사고 목록:")
                for idx, incident in enumerate(data['incidents'][:5], 1):
                    print(f"   {idx}. ID: {incident['id']}, 타입: {incident['incident_type']}, "
                          f"신뢰도: {incident['confidence']:.2f}")
            
            return True
        else:
            print(f"❌ 사고 목록 조회 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 사고 목록 조회 오류: {e}")
        return False


def test_dashboard_stats():
    """대시보드 통계 테스트"""
    print("\n" + "=" * 60)
    print("6️⃣  대시보드 통계 테스트")
    print("=" * 60)
    
    try:
        # 로그인
        login_response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={'id': 'admin', 'password': 'admin123'},
            timeout=5
        )
        
        if login_response.status_code != 200:
            print(f"⚠️  로그인 실패")
            return False
        
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 대시보드 통계 조회
        response = requests.get(
            f"{BACKEND_URL}/api/dashboard/stats",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 대시보드 통계 조회 성공!")
            print(f"   전체 영상: {data['totalVideos']}개")
            print(f"   확인된 영상: {data['checkedVideos']}개")
            print(f"   미확인 영상: {data['uncheckedVideos']}개")
            print(f"   오늘 영상: {data['todayVideos']}개")
            print(f"   확인률: {data['checkRate']:.1f}%")
            print(f"   시스템 상태: {data['system_status']}")
            return True
        else:
            print(f"❌ 대시보드 통계 조회 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 대시보드 통계 오류: {e}")
        return False


def test_video_sync():
    """비디오 동기화 테스트"""
    print("\n" + "=" * 60)
    print("7️⃣  비디오 동기화 테스트")
    print("=" * 60)
    
    try:
        # 로그인
        login_response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={'id': 'admin', 'password': 'admin123'},
            timeout=5
        )
        
        if login_response.status_code != 200:
            print(f"⚠️  로그인 실패")
            return False
        
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 비디오 동기화
        response = requests.post(
            f"{BACKEND_URL}/api/videos/sync",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 비디오 동기화 성공!")
            print(f"   전체 비디오 파일: {data['total_videos']}개")
            print(f"   DB 등록된 비디오: {data['db_videos_before']}개")
            print(f"   누락 발견: {data['missing_found']}개")
            print(f"   새로 등록: {data['registered']}개")
            print(f"   등록 실패: {data['failed']}개")
            return True
        else:
            print(f"❌ 비디오 동기화 실패: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 비디오 동기화 오류: {e}")
        return False


def test_stream_status():
    """스트리밍 상태 확인 테스트"""
    print("\n" + "=" * 60)
    print("8️⃣  스트리밍 상태 확인 테스트")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/dashboard/stream/status",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 스트리밍 상태 조회 성공!")
            print(f"   활성 여부: {data['stream_active']}")
            print(f"   상태: {data['status']}")
            
            if data['stream_active'] and 'session' in data:
                session = data['session']
                print(f"   세션 ID: {session['id']}")
                print(f"   디바이스 ID: {session['device_id']}")
                print(f"   총 프레임: {session['total_frames']}개")
            
            return True
        else:
            print(f"❌ 스트리밍 상태 조회 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 스트리밍 상태 오류: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("🚀 SafeFall 통합 테스트 시작")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Device ID: {DEVICE_ID}")
    
    results = {}
    
    # 1. 백엔드 연결 테스트
    results['connection'] = test_backend_connection()
    if not results['connection']:
        print("\n❌ 백엔드 연결 실패. 테스트를 중단합니다.")
        return
    
    time.sleep(1)
    
    # 2. 스트리밍 세션 시작
    results['session'] = test_stream_session()
    time.sleep(1)
    
    # 3. 프레임 업로드
    results['upload'] = test_frame_upload()
    time.sleep(1)
    
    # 4. 사고 신고
    incident_id = test_incident_report()
    results['incident'] = incident_id is not None
    time.sleep(1)
    
    # 5. 사고 목록 조회
    if incident_id:
        results['list'] = test_incident_list(incident_id)
    else:
        print("\n⚠️  사고 ID가 없어 목록 조회를 건너뜁니다.")
        results['list'] = False
    time.sleep(1)
    
    # 6. 대시보드 통계
    results['dashboard'] = test_dashboard_stats()
    time.sleep(1)
    
    # 7. 비디오 동기화
    results['sync'] = test_video_sync()
    time.sleep(1)
    
    # 8. 스트리밍 상태
    results['stream_status'] = test_stream_status()
    
    # 최종 결과
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name:20s}: {status}")
    
    print("=" * 60)
    print(f"총 {total_tests}개 테스트 중 {passed_tests}개 성공 "
          f"({passed_tests / total_tests * 100:.1f}%)")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("\n🎉 모든 테스트 통과! 시스템이 정상 작동합니다.")
    elif passed_tests > 0:
        print(f"\n⚠️  일부 테스트 실패. {total_tests - passed_tests}개 항목을 확인하세요.")
    else:
        print("\n❌ 모든 테스트 실패. 시스템 설정을 확인하세요.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
