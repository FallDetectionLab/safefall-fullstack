import threading
from collections import deque
from datetime import datetime, timedelta, timezone
import time


class CircularVideoBuffer:
    """
    순환 버퍼 - 사고 발생 전 15초 영상을 메모리에 보관
    """
    
    def __init__(self, duration=15, fps=30):
        """
        Args:
            duration: 버퍼에 보관할 시간 (초)
            fps: 초당 프레임 수
        """
        self.duration = duration
        self.fps = fps
        self.max_frames = duration * fps  # 15초 * 30fps = 450 프레임
        
        self.buffer = deque(maxlen=self.max_frames)
        self.lock = threading.Lock()
        
        print(f"📦 순환 버퍼 초기화: {duration}초, {fps}FPS, 최대 {self.max_frames} 프레임")
    
    def add_frame(self, frame_data, timestamp=None):
        """
        프레임 추가
        
        Args:
            frame_data: 프레임 데이터 (바이트 또는 numpy array)
            timestamp: 타임스탬프 (None이면 현재 시각)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        with self.lock:
            self.buffer.append({
                'data': frame_data,
                'timestamp': timestamp
            })
    
    def get_frames_before(self, incident_time, duration=15):
        """
        특정 시각 이전의 프레임들 반환
        
        Args:
            incident_time: 사고 발생 시각
            duration: 가져올 시간 (초)
        
        Returns:
            list: 프레임 리스트
        """
        if incident_time.tzinfo is None:
            incident_time = incident_time.replace(tzinfo=timezone.utc)
        
        cutoff_time = incident_time - timedelta(seconds=duration)
        
        with self.lock:
            frames = [
                frame for frame in self.buffer
                if cutoff_time <= frame['timestamp'] <= incident_time
            ]
        
        return frames
    
    def get_all_frames(self):
        """버퍼의 모든 프레임 반환"""
        with self.lock:
            return list(self.buffer)
    
    def clear(self):
        """버퍼 초기화"""
        with self.lock:
            self.buffer.clear()
    
    def get_status(self):
        """버퍼 상태 반환"""
        with self.lock:
            frame_count = len(self.buffer)
            if frame_count > 0:
                oldest = self.buffer[0]['timestamp']
                newest = self.buffer[-1]['timestamp']
                duration_seconds = (newest - oldest).total_seconds()
            else:
                oldest = newest = None
                duration_seconds = 0
        
        return {
            'frame_count': frame_count,
            'max_frames': self.max_frames,
            'duration_seconds': duration_seconds,
            'oldest_frame': oldest.isoformat() if oldest else None,
            'newest_frame': newest.isoformat() if newest else None,
            'usage_percent': round((frame_count / self.max_frames) * 100, 2)
        }


class HLSSegmentManager:
    """
    HLS 세그먼트 관리자
    """
    
    def __init__(self, output_dir, segment_duration=2):
        """
        Args:
            output_dir: HLS 파일 저장 경로
            segment_duration: 세그먼트 길이 (초)
        """
        self.output_dir = output_dir
        self.segment_duration = segment_duration
        self.current_sequence = 0
        self.segments = []
        self.lock = threading.Lock()
        
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"📺 HLS 세그먼트 매니저 초기화: {output_dir}")
    
    def add_segment(self, segment_path):
        """세그먼트 추가"""
        with self.lock:
            self.segments.append({
                'path': segment_path,
                'sequence': self.current_sequence,
                'timestamp': datetime.now(timezone.utc)
            })
            self.current_sequence += 1
            
            # 오래된 세그먼트 제거 (최근 10개만 유지)
            if len(self.segments) > 10:
                old_segment = self.segments.pop(0)
                # 파일 삭제는 별도로 처리
    
    def get_playlist(self):
        """M3U8 플레이리스트 생성"""
        with self.lock:
            playlist = "#EXTM3U\n"
            playlist += "#EXT-X-VERSION:3\n"
            playlist += f"#EXT-X-TARGETDURATION:{self.segment_duration}\n"
            playlist += "#EXT-X-MEDIA-SEQUENCE:0\n"
            
            for segment in self.segments:
                playlist += f"#EXTINF:{self.segment_duration}.0,\n"
                playlist += f"{segment['path']}\n"
            
            return playlist
    
    def clear(self):
        """세그먼트 초기화"""
        with self.lock:
            self.segments.clear()
            self.current_sequence = 0