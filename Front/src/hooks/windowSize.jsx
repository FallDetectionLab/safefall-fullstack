/**
 * 브라우저 윈도우 크기 추적 커스텀 훅
 * - 반응형 레이아웃을 위한 현재 윈도우 width/height 제공
 * - 디바운싱 적용 (150ms)으로 성능 최적화
 * - 리사이즈 이벤트 자동 cleanup
 */
import { useState, useEffect } from 'react';

function WindowSize() {
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    // ✅ PERFORMANCE FIX: 디바운싱을 적용한 리사이즈 핸들러
    // 리사이즈 이벤트가 빈번하게 발생하는 것을 방지하여 성능 최적화
    let timeoutId = null;

    const handleResize = () => {
      // 이전 타이머가 있으면 취소
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      // 새로운 타이머 설정 (150ms 후에 실행)
      timeoutId = setTimeout(() => {
        setWindowSize({
          width: window.innerWidth,
          height: window.innerHeight,
        });
      }, 150);
    };

    // 이벤트 리스너 등록
    window.addEventListener('resize', handleResize);

    // cleanup 함수 - 이벤트 리스너 제거 및 대기 중인 타이머 취소
    return () => {
      window.removeEventListener('resize', handleResize);
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, []);

  return windowSize;
}

export default WindowSize;