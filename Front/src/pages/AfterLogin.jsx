/**
 * 로그인 후 대시보드 메인 페이지 컴포넌트
 * - 라즈베리파이 스켈레톤 스트림 표시 ⭐
 * - 최근 낙상 영상 6개 목록 표시
 * - 월별 통계 그래프 (DBGraph) 표시
 * - 더보기 버튼으로 CheckHistory 페이지 이동
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  getStreamStatus,
  getDashboardStats,
  getRecentVideos as getRecentVideosAPI,
  getLastPositiveDetection
} from "../services/api";

import DBGraph from "../components/DBGraph";  // 🔥 DBGraph 컴포넌트 추가
import LiveVideo from "../components/LiveVideo";
import WindowSize from "../hooks/windowSize";  // 🔥 WindowSize 훅 추가
import VideoBtnSmall from "../components/SVG-VideoBtnSmall";  // 🔥 VideoBtnSmall 컴포넌트 추가

import "./AfterLogin.css";

// 백엔드 URL 환경변수 설정
const BACKEND_BASE = import.meta.env.VITE_BACKEND_URL || 'http://43.203.245.90:8000';

// ⭐ 라즈베리파이 스트리밍 URL
const RASPBERRY_PI_STREAM_URL = 'http://192.168.102.67:5001/video_feed';

const AfterLogin = ({ 
  incidentVideos: incidentVideosProp,
  LiveVideoComponent,
  liveVideoConfig,
  getRecentVideos: getRecentVideosProp,
  refreshIncidentVideos  // 🔥 데이터 새로고침 함수 추가
}) => {
  const [windowSizeTF, setWindowSizeTF] = useState(false);
  const [incidentVideos, setIncidentVideos] = useState([]);
  const { width } = WindowSize();
  const navigate = useNavigate();

  useEffect(() => {
    setWindowSizeTF(!(width >= 1200));
  }, [width]);

  // 최근 낙상 영상 6개 불러오기
  useEffect(() => {
    if (Array.isArray(incidentVideosProp) && incidentVideosProp.length) {
      setIncidentVideos(incidentVideosProp);
      return;
    }

    (async () => {
      try {
        const res = await getRecentVideosAPI(6);
        console.log('API 비디오 데이터:', res); // 디버그용
        
        if (res && res.success && res.data) {
          console.log('비디오 데이터 설정:', res.data);
          // MP4 파일만 필터링
          const mp4Videos = res.data.filter(video => 
            video.filename && video.filename.toLowerCase().endsWith('.mp4')
          );
          console.log(`🎬 MP4 영상 필터링: ${res.data.length}개 → ${mp4Videos.length}개`);
          setIncidentVideos(mp4Videos);
        } else if (Array.isArray(res)) {
          // MP4 파일만 필터링
          const mp4Videos = res.filter(video => 
            video.filename && video.filename.toLowerCase().endsWith('.mp4')
          );
          console.log(`🎬 MP4 영상 필터링: ${res.length}개 → ${mp4Videos.length}개`);
          setIncidentVideos(mp4Videos);
        } else {
          console.log('비디오 데이터 없음, 빈 배열 설정');
          setIncidentVideos([]);
        }
      } catch (e) {
        console.warn("Failed to load recent fall videos:", e?.message || e);
        setIncidentVideos([]);
      }
    })();
  }, [incidentVideosProp]);

  const getRecentSixVideos = () => {
    if (typeof getRecentVideosProp === "function") {
      const out = getRecentVideosProp(6);
      return Array.isArray(out) ? out : [];
    }
    return (incidentVideos || [])
      .slice()
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
      .slice(0, 6);
  };

  const handleMoreVideos = async () => {
    console.log('📝 더보기 버튼 클릭 - 데이터 새로고침 후 CheckHistory 페이지로 이동');
    
    try {
      // 1단계: 데이터 새로고침 (녹화 중인 영상도 포함)
      if (refreshIncidentVideos) {
        console.log('🔄 대시보드에서 데이터 새로고침 시작...');
        await refreshIncidentVideos();
        console.log('✅ 대시보드에서 데이터 새로고침 완료');
      }
      
      // 2단계: 페이지 이동
      console.log('📝 CheckHistory 페이지로 이동');
      navigate('/history');
      
    } catch (error) {
      console.error('❌ 대시보드 데이터 새로고침 오류:', error);
      // 에러가 있어도 페이지는 이동
      navigate('/history');
    }
  };

  const handleVideoClick = (item) => {
    navigate(`/video/${encodeURIComponent(item.id)}`);
  };

  return (
    <div className="AfterLoginWindowDesktop">
      {/* ⭐ 라즈베리파이 스켈레톤 실시간 스트림만 표시 */}
      <div className="realtimevideoBox">
        <img 
          src={RASPBERRY_PI_STREAM_URL}
          alt="Raspberry Pi Skeleton Detection Stream"
          style={{
            display: 'block',
            width: '100%',
            height: 'auto',
            borderRadius: '8px',
            background: '#000'
          }}
          onError={(e) => {
            console.error('라즈베리파이 스트림 로딩 실패');
            e.target.style.opacity = '0.5';
          }}
        />
      </div>

      <div className="listAndGraphWindowDesktop">
        <div className="listWindowDesktop">
          <h3>기록보기</h3>
          <ul className="DBlistSmall">
            {getRecentSixVideos().map((item, index) => (
              <li
                key={`${item.id}-${item.filename}-${index}`}
                onClick={() => handleVideoClick(item)}
                style={{ cursor: "pointer" }}
              >
                {windowSizeTF ? (
                  <>
                    <div className="sumnailBox">
                      <VideoBtnSmall />
                    </div>
                    <div className="DBListInfoBox">
                      <p className="DBListFilename">{item.filename}</p>
                      <p className="DBListCreatedAt">{item.createdAt}</p>
                      <div className="checkline">
                        <p>확인 여부</p>
                        <div
                          className={
                            item.isChecked || item.processed
                              ? "checkBoxSmall checkFinish"
                              : "checkBoxSmall checkPrev"
                          }
                        >
                          {item.isChecked || item.processed ? "완료" : "대기"}
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <p>
                      <span>
                        <VideoBtnSmall />
                      </span>
                      {item.filename}
                    </p>
                    <div
                      className={
                        item.isChecked || item.processed
                          ? "checkBoxSmall checkFinish"
                          : "checkBoxSmall checkPrev"
                      }
                    >
                      {item.isChecked || item.processed ? "완료" : "대기"}
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>
          <button onClick={handleMoreVideos}>더보기</button>
        </div>
        <div className="graphWindowDesktop">
          <DBGraph incidentVideos={incidentVideos} />
        </div>
      </div>
    </div>
  );
};

export default AfterLogin;
