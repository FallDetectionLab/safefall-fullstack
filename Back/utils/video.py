import cv2
import numpy as np
import os
from datetime import datetime
import subprocess
from pathlib import Path


def frames_to_video(frames, output_path, fps=None):
    """
    프레임 리스트를 MP4 비디오로 저장 (웹 호환 H.264 코덱)
    
    Args:
        frames: 프레임 리스트 (각 프레임은 {'data': numpy_array, 'timestamp': datetime})
        output_path: 출력 비디오 경로
        fps: 초당 프레임 수 (None이면 자동 계산)
    
    Returns:
        bool: 성공 여부
    """
    if not frames:
        print("❌ 저장할 프레임이 없습니다")
        return False
    
    try:
        # 첫 프레임으로 크기 확인
        first_frame = frames[0]['data']
        if isinstance(first_frame, bytes):
            # JPEG 바이트인 경우 디코드
            nparr = np.frombuffer(first_frame, np.uint8)
            first_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        height, width = first_frame.shape[:2]
        
        # FPS 자동 계산 (타임스탬프 기반)
        if fps is None and len(frames) > 1:
            # 첫 프레임과 마지막 프레임의 시간 차이로 실제 FPS 계산
            time_diff = (frames[-1]['timestamp'] - frames[0]['timestamp']).total_seconds()
            if time_diff > 0:
                fps = len(frames) / time_diff
                print(f"📊 실제 FPS 계산: {fps:.2f} ({len(frames)} 프레임 / {time_diff:.2f}초)")
            else:
                fps = 30  # 기본값
                print(f"⚠️ 타임스탬프 차이 없음, 기본 FPS 사용: {fps}")
        elif fps is None:
            fps = 30  # 단일 프레임인 경우 기본값
        
        # 임시 파일 경로 (mp4v 코덱으로 먼저 저장)
        temp_path = output_path.replace('.mp4', '_temp.mp4')
        
        # VideoWriter 설정 - 먼저 mp4v로 저장
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            print("❌ VideoWriter 초기화 실패")
            return False
        
        # 프레임 쓰기
        for frame_data in frames:
            frame = frame_data['data']
            
            # 바이트 데이터면 디코드
            if isinstance(frame, bytes):
                nparr = np.frombuffer(frame, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            out.write(frame)
        
        out.release()
        
        # 임시 파일이 제대로 생성되었는지 확인
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            print(f"❌ 임시 비디오 파일 생성 실패: {temp_path}")
            return False
        
        print(f"✅ 임시 파일 생성 완료: {temp_path} ({len(frames)} 프레임)")
        
        # ffmpeg으로 H.264 코덱으로 변환 (웹 호환)
        success = convert_to_web_compatible(temp_path, output_path)
        
        # 임시 파일 삭제
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"🗑️ 임시 파일 삭제: {temp_path}")
        except Exception as e:
            print(f"⚠️ 임시 파일 삭제 실패: {e}")
        
        if success:
            print(f"✅ 웹 호환 비디오 저장 완료: {output_path}")
            return True
        else:
            # ffmpeg 실패 시 임시 파일을 그대로 사용
            print(f"⚠️ ffmpeg 변환 실패, 임시 파일 사용")
            if os.path.exists(temp_path):
                os.rename(temp_path, output_path)
                return True
            return False
        
    except Exception as e:
        print(f"❌ 비디오 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def convert_to_web_compatible(input_path, output_path):
    """
    비디오를 웹 호환 H.264 코덱으로 변환
    
    Args:
        input_path: 입력 비디오 경로
        output_path: 출력 비디오 경로
    
    Returns:
        bool: 성공 여부
    """
    try:
        # ffmpeg 명령어
        # -c:v libx264: H.264 비디오 코덱
        # -preset fast: 빠른 인코딩
        # -crf 23: 품질 설정 (낮을수록 고품질, 23은 기본값)
        # -movflags +faststart: 웹 스트리밍 최적화 (moov atom을 파일 앞쪽으로)
        # -pix_fmt yuv420p: 브라우저 호환성을 위한 픽셀 포맷
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            '-y',  # 덮어쓰기
            output_path
        ]
        
        print(f"🔄 ffmpeg 변환 시작: {input_path} → {output_path}")
        
        # ffmpeg 실행
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60초 타임아웃
        )
        
        if result.returncode == 0:
            # 변환된 파일 검증
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"✅ ffmpeg 변환 완료: {output_path} ({file_size_mb:.2f} MB)")
                return True
            else:
                print(f"❌ 변환된 파일이 유효하지 않음: {output_path}")
                return False
        else:
            print(f"❌ ffmpeg 변환 실패:")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ ffmpeg를 찾을 수 없습니다. ffmpeg가 설치되어 있고 PATH에 등록되어 있는지 확인하세요.")
        print("   설치: https://ffmpeg.org/download.html")
        return False
    except subprocess.TimeoutExpired:
        print("❌ ffmpeg 변환 시간 초과 (60초)")
        return False
    except Exception as e:
        print(f"❌ ffmpeg 변환 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def batch_convert_videos(directory):
    """
    디렉토리 내의 모든 비디오를 웹 호환 포맷으로 변환
    
    Args:
        directory: 비디오 디렉토리 경로
    
    Returns:
        dict: 변환 통계
    """
    if not os.path.exists(directory):
        return {'error': f'디렉토리가 존재하지 않습니다: {directory}'}
    
    video_files = [f for f in os.listdir(directory) if f.endswith('.mp4')]
    
    if not video_files:
        return {'message': '변환할 비디오가 없습니다', 'converted': 0}
    
    print(f"\n{'='*60}")
    print(f"🎬 비디오 일괄 변환 시작: {len(video_files)}개 파일")
    print(f"📁 디렉토리: {directory}")
    print(f"{'='*60}\n")
    
    stats = {
        'total': len(video_files),
        'converted': 0,
        'skipped': 0,
        'failed': 0,
        'errors': []
    }
    
    for i, filename in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] 처리 중: {filename}")
        
        input_path = os.path.join(directory, filename)
        
        # 백업 파일 생성
        backup_path = input_path.replace('.mp4', '_original.mp4')
        temp_output = input_path.replace('.mp4', '_converted.mp4')
        
        try:
            # 원본을 백업으로 복사
            import shutil
            shutil.copy2(input_path, backup_path)
            print(f"💾 백업 생성: {os.path.basename(backup_path)}")
            
            # ffmpeg으로 변환
            if convert_to_web_compatible(input_path, temp_output):
                # 변환 성공 시 원본을 변환된 파일로 교체
                os.remove(input_path)
                os.rename(temp_output, input_path)
                
                # 백업 파일 삭제
                os.remove(backup_path)
                
                stats['converted'] += 1
                print(f"✅ 변환 완료: {filename}")
            else:
                # 변환 실패 시 백업 복원
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                
                stats['failed'] += 1
                stats['errors'].append(f"{filename}: 변환 실패")
                print(f"❌ 변환 실패: {filename}")
                
        except Exception as e:
            # 에러 발생 시 백업 복원
            if os.path.exists(backup_path):
                if os.path.exists(input_path):
                    os.remove(input_path)
                os.rename(backup_path, input_path)
            
            stats['failed'] += 1
            stats['errors'].append(f"{filename}: {str(e)}")
            print(f"❌ 오류 발생: {filename} - {e}")
    
    print(f"\n{'='*60}")
    print(f"🎬 변환 완료!")
    print(f"   ✅ 성공: {stats['converted']}개")
    print(f"   ⏭️ 건너뜀: {stats['skipped']}개")
    print(f"   ❌ 실패: {stats['failed']}개")
    print(f"{'='*60}\n")
    
    return stats


def create_thumbnail(video_path, thumbnail_path, time_offset=0):
    """
    비디오에서 썸네일 생성
    
    Args:
        video_path: 비디오 파일 경로
        thumbnail_path: 썸네일 저장 경로
        time_offset: 썸네일 추출 시간 (초)
    
    Returns:
        bool: 성공 여부
    """
    try:
        # 비디오 파일 존재 확인
        if not os.path.exists(video_path):
            print(f"❌ 비디오 파일이 존재하지 않습니다: {video_path}")
            return False
        
        # 비디오 열기
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"❌ 비디오를 열 수 없습니다: {video_path}")
            return False
        
        # 비디오 정보 확인
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if total_frames == 0 or fps == 0:
            print(f"❌ 비디오 정보를 읽을 수 없습니다 (frames: {total_frames}, fps: {fps})")
            cap.release()
            return False
        
        # 중간 프레임으로 이동 (time_offset이 0이면 중간 프레임 사용)
        if time_offset == 0:
            frame_number = total_frames // 2
        else:
            frame_number = min(int(time_offset * fps), total_frames - 1)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            # 썸네일 크기 조정 (640x360)
            thumbnail = cv2.resize(frame, (640, 360))
            
            # 썸네일 저장
            success = cv2.imwrite(thumbnail_path, thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            if success:
                print(f"✅ 썸네일 생성 완료: {thumbnail_path}")
                return True
            else:
                print(f"❌ 썸네일 저장 실패: {thumbnail_path}")
                return False
        else:
            print(f"❌ 프레임 읽기 실패 (frame_number: {frame_number}/{total_frames})")
            return False
            
    except Exception as e:
        print(f"❌ 썸네일 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_video_info(video_path):
    """
    비디오 정보 추출
    
    Args:
        video_path: 비디오 파일 경로
    
    Returns:
        dict: 비디오 정보
    """
    try:
        if not os.path.exists(video_path):
            print(f"❌ 비디오 파일이 존재하지 않습니다: {video_path}")
            return None
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"❌ 비디오를 열 수 없습니다: {video_path}")
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        file_size = os.path.getsize(video_path)
        
        return {
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'duration': duration,
            'file_size': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        print(f"❌ 비디오 정보 추출 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


# 스크립트로 직접 실행 시 일괄 변환 수행
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        # 기본 경로
        directory = os.path.join(os.path.dirname(__file__), '..', 'videos')
        directory = os.path.abspath(directory)
    
    print(f"📁 비디오 디렉토리: {directory}")
    
    result = batch_convert_videos(directory)
    
    if 'error' in result:
        print(f"❌ {result['error']}")
        sys.exit(1)
    else:
        print(f"\n최종 결과: {result}")
        sys.exit(0)
