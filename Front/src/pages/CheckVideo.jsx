import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";

import WindowSize from "../hooks/windowSize";
import VideoBtnSmall from "../components/SVG-VideoBtnSmall";

import "./CheckVideo.css";

function CheckVideo({
  incidentVideos = [],
  updateVideoCheckStatus,
  LiveVideoComponent,
}) {
  const { id, filename } = useParams();
  const navigate = useNavigate();
  const { width } = WindowSize();
  const videoRef = useRef(null);

  const [videoData, setVideoData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [videoUrl, setVideoUrl] = useState(null);
  const [videoError, setVideoError] = useState(null);
  const [debugInfo, setDebugInfo] = useState(null);

  // API에서 직접 영상 정보 가져오기
  useEffect(() => {
    const loadVideoData = async () => {
      if (id || filename) {
        try {
          const identifier = id || filename;
          console.log('🔍 Loading video for:', identifier);
          
          setDebugInfo(`Loading: ${identifier}`);
          
          // ✅ API를 항상 먼저 사용
          const token = localStorage.getItem('access_token');
          const apiUrl = `http://localhost:5001/api/incidents/${encodeURIComponent(identifier)}`;
          
          console.log('📡 Fetching from:', apiUrl);
          setDebugInfo(`Fetching from: ${apiUrl}`);
          
          const response = await fetch(apiUrl, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          console.log('📦 Response status:', response.status);
          setDebugInfo(`Response status: ${response.status}`);
          
          if (response.ok) {
            const data = await response.json();
            console.log('📦 API Response:', data);
            
            if (data.success && data.video) {
              const video = data.video;
              setVideoData(video);
              
              // ✅ URL 설정 - 타임스탬프 제거, 깔끔한 URL 사용
              const finalUrl = video.url || `/api/incidents/${video.id}/video`;
              // localhost:5000을 명시적으로 포함
              const fullUrl = finalUrl.startsWith('http') 
                ? finalUrl 
                : `http://localhost:5001${finalUrl}`;
              
              console.log('✅ Video URL:', fullUrl);
              setDebugInfo(`Video URL: ${fullUrl}`);
              setVideoUrl(fullUrl);
              setLoading(false);
              return;
            }
          } else {
            const errorText = await response.text();
            console.error('❌ API Error:', errorText);
            setDebugInfo(`API Error: ${response.status} - ${errorText}`);
          }
          
          // API 실패 시에만 incidentVideos 사용
          if (incidentVideos.length > 0) {
            console.log('🔄 Falling back to incidentVideos');
            setDebugInfo('Falling back to incidentVideos');
            
            let foundVideo = null;
            
            if (id && !isNaN(id)) {
              foundVideo = incidentVideos.find((v) => String(v.id) === String(id));
            }
            
            if (!foundVideo && (filename || id)) {
              const searchFilename = filename || id;
              const decodedFilename = decodeURIComponent(searchFilename);
              foundVideo = incidentVideos.find((v) => 
                v.filename === decodedFilename || v.filename === searchFilename
              );
            }
            
            if (foundVideo) {
              setVideoData(foundVideo);
              const finalUrl = foundVideo.url || `/api/incidents/${foundVideo.id}/video`;
              const fullUrl = finalUrl.startsWith('http') 
                ? finalUrl 
                : `http://localhost:5001${finalUrl}`;
              
              console.log('✅ Fallback Video URL:', fullUrl);
              setVideoUrl(fullUrl);
              setLoading(false);
              return;
            }
          }
          
          setVideoError('영상을 찾을 수 없습니다.');
          setDebugInfo('Video not found in API or local cache');
          setLoading(false);
          
        } catch (error) {
          console.error('❌ Load error:', error);
          setVideoError(error.message);
          setDebugInfo(`Load error: ${error.message}`);
          setLoading(false);
        }
      }
    };
    
    loadVideoData();
  }, [id, filename, incidentVideos]);

  const handleGoBack = () => navigate(-1);

  const handleToggleCheck = () => {
    if (videoData && updateVideoCheckStatus) {
      const newCheckStatus = !videoData.isChecked;
      updateVideoCheckStatus(videoData.id ?? videoData.filename, newCheckStatus);
      setVideoData((prev) => ({ ...prev, isChecked: newCheckStatus }));
    }
  };

  const handlePlayToggle = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        // 명시적으로 재생 시도
        const playPromise = videoRef.current.play();
        
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              console.log('✅ Video playback started successfully');
            })
            .catch(error => {
              console.error('❌ Play error:', error);
              // NotAllowedError: 브라우저가 자동 재생을 차단
              // NotSupportedError: 비디오 형식이 지원되지 않음
              if (error.name === 'NotAllowedError') {
                setVideoError('브라우저가 자동 재생을 차단했습니다. 재생 버튼을 다시 클릭해주세요.');
              } else if (error.name === 'NotSupportedError') {
                setVideoError('비디오 형식이 지원되지 않습니다. 비디오를 H.264 코덱으로 변환하세요.');
              } else if (error.name === 'AbortError') {
                // 재생이 중단됨 - 무시 (정상적인 상황)
                console.log('⚠️ Play aborted - video might be reloading');
              } else {
                setVideoError(`영상 재생 중 오류가 발생했습니다: ${error.message}`);
              }
              setDebugInfo(`Play error: ${error.name} - ${error.message}`);
            });
        }
      }
    }
  };

  const handleVideoPlay = () => {
    console.log('✅ Video started playing');
    setIsPlaying(true);
    setVideoError(null); // 재생 성공 시 에러 메시지 제거
  };

  const handleVideoPause = () => {
    console.log('⏸️ Video paused');
    setIsPlaying(false);
  };

  const handleVideoTimeUpdate = () => {
    if (videoRef.current) setCurrentTime(videoRef.current.currentTime);
  };

  const handleVideoLoadedMetadata = () => {
    if (videoRef.current) {
      console.log('✅ Video metadata loaded:', {
        duration: videoRef.current.duration,
        videoWidth: videoRef.current.videoWidth,
        videoHeight: videoRef.current.videoHeight
      });
      setDuration(videoRef.current.duration);
    }
  };

  const handleVideoError = (e) => {
    console.error('❌ Video error:', e);
    
    let errorMessage = '영상을 로드할 수 없습니다.';
    let debugMessage = '';
    
    if (e.target?.error) {
      const errorCode = e.target.error.code;
      const errorName = e.target.error.message;
      
      console.error('Error details:', {
        code: errorCode,
        message: errorName,
        src: e.target.src,
        networkState: e.target.networkState,
        readyState: e.target.readyState
      });
      
      switch(errorCode) {
        case 1: // MEDIA_ERR_ABORTED
          errorMessage += ' 사용자가 중단했습니다.';
          debugMessage = `MEDIA_ERR_ABORTED (${errorCode})`;
          break;
        case 2: // MEDIA_ERR_NETWORK
          errorMessage += ' 네트워크 오류.';
          debugMessage = `MEDIA_ERR_NETWORK (${errorCode}) - 서버 연결 확인 필요`;
          break;
        case 3: // MEDIA_ERR_DECODE
          errorMessage += ' 디코딩 오류. 비디오 코덱을 H.264로 변환하세요.';
          debugMessage = `MEDIA_ERR_DECODE (${errorCode}) - 코덱 문제. ffmpeg 변환 필요`;
          break;
        case 4: // MEDIA_ERR_SRC_NOT_SUPPORTED
          errorMessage += ' 지원되지 않는 형식. 비디오를 H.264 코덱으로 변환하세요.';
          debugMessage = `MEDIA_ERR_SRC_NOT_SUPPORTED (${errorCode}) - H.264 코덱으로 변환 필요`;
          break;
        default:
          errorMessage += ' 알 수 없는 오류.';
          debugMessage = `Unknown error (${errorCode})`;
      }
    }
    
    setVideoError(errorMessage);
    setDebugInfo(debugMessage);
  };

  const handleVideoCanPlay = () => {
    console.log('✅ Video can play - buffered enough data');
    setDebugInfo('Video ready to play');
  };

  const handleProgressClick = (e) => {
    if (videoRef.current && duration > 0) {
      const rect = e.currentTarget.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickRatio = clickX / rect.width;
      videoRef.current.currentTime = clickRatio * duration;
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return `${date.getFullYear()}년 ${String(date.getMonth() + 1).padStart(2, "0")}월 ${String(date.getDate()).padStart(2, "0")}일 ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
  };

  const formatTime = (timeInSeconds) => {
    if (isNaN(timeInSeconds)) return '0:00';
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${minutes}:${String(seconds).padStart(2, '0')}`;
  };

  const getFileSize = () => {
    return videoData?.size ? `${Math.round(videoData.size / 1024 / 1024)}MB` : 'N/A';
  };

  // 새 탭에서 열기 (디버깅용)
  const openInNewTab = () => {
    if (videoUrl) {
      window.open(videoUrl, '_blank');
    }
  };

  // 직접 테스트 (디버깅용)
  const testUrl = async () => {
    if (!videoUrl) return;
    
    console.log('🧪 Testing video URL:', videoUrl);
    setDebugInfo('Testing URL...');
    
    try {
      const response = await fetch(videoUrl, {
        method: 'HEAD' // HEAD 요청으로 파일 존재 확인
      });
      
      console.log('🧪 Test result:', {
        status: response.status,
        contentType: response.headers.get('Content-Type'),
        contentLength: response.headers.get('Content-Length'),
        acceptRanges: response.headers.get('Accept-Ranges')
      });
      
      if (response.ok) {
        setDebugInfo(`✅ URL 접근 가능 (${response.status}) - ${response.headers.get('Content-Type')}`);
      } else {
        setDebugInfo(`❌ URL 접근 실패 (${response.status})`);
      }
    } catch (error) {
      console.error('🧪 Test error:', error);
      setDebugInfo(`❌ URL 테스트 오류: ${error.message}`);
    }
  };

  if (loading) {
    return (
      <div className="checkVideoPage">
        <div className="loading">
          <p>영상 정보를 불러오는 중...</p>
          {debugInfo && <p style={{fontSize: '12px', color: '#666'}}>{debugInfo}</p>}
        </div>
      </div>
    );
  }

  if (!videoData) {
    return (
      <div className="checkVideoPage">
        <div className="notFound">
          <h2>영상을 찾을 수 없습니다</h2>
          {debugInfo && <p style={{fontSize: '12px', color: '#666', marginTop: '10px'}}>{debugInfo}</p>}
          <button onClick={handleGoBack}>뒤로가기</button>
        </div>
      </div>
    );
  }

  return (
    <div className="checkVideoPage">
      <div className="videoHeader">
        <button className="backButton" onClick={handleGoBack} style={{ border: "none", background: "none", fontSize: "24px", cursor: "pointer" }}>←</button>
        <h1>영상 상세 정보</h1>
      </div>

      <div className="videoContent">
        <div className="videoPlayerSection">
          <div className="videoPlayer">
            {videoError ? (
              <div className="videoError">
                <VideoBtnSmall />
                <p>{videoError}</p>
                {debugInfo && <p style={{fontSize: '12px', color: '#999', marginTop: '10px'}}>{debugInfo}</p>}
                <p style={{fontSize: '12px', color: '#666', marginTop: '10px', wordBreak: 'break-all'}}>
                  URL: {videoUrl}
                </p>
                <div style={{display: 'flex', gap: '10px', marginTop: '10px', flexWrap: 'wrap'}}>
                  <button 
                    onClick={openInNewTab}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#007bff',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    새 탭에서 열기
                  </button>
                  <button 
                    onClick={testUrl}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    URL 테스트
                  </button>
                  <button 
                    onClick={() => {
                      setVideoError(null);
                      window.location.reload();
                    }}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#ffc107',
                      color: 'black',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    페이지 새로고침
                  </button>
                </div>
              </div>
            ) : videoUrl ? (
              <video
                ref={videoRef}
                src={videoUrl}
                onPlay={handleVideoPlay}
                onPause={handleVideoPause}
                onTimeUpdate={handleVideoTimeUpdate}
                onLoadedMetadata={handleVideoLoadedMetadata}
                onError={handleVideoError}
                onCanPlay={handleVideoCanPlay}
                playsInline
                preload="metadata"
                style={{ width: '100%', height: '100%', objectFit: 'contain', backgroundColor: '#000' }}
              />
            ) : (
              <div className="videoPlaceholder">
                <VideoBtnSmall />
                <p>영상을 로드하는 중...</p>
              </div>
            )}

            {!isPlaying && videoUrl && !videoError && (
              <div className="playOverlay" onClick={handlePlayToggle} style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.3)', cursor: 'pointer' }}>
                <div className="playButton" style={{fontSize: '48px', color: 'white', userSelect: 'none'}}>▶</div>
              </div>
            )}
          </div>

          <div className="videoControls">
            <button className={`playBtn ${isPlaying ? "playing" : ""}`} onClick={handlePlayToggle} disabled={!videoUrl || videoError}>
              {isPlaying ? "⏸ 정지" : "▶ 재생"}
            </button>
            <div className="videoProgress">
              <div className="progressBar" onClick={handleProgressClick} style={{ cursor: 'pointer' }}>
                <div className="progress" style={{ width: duration > 0 ? `${(currentTime / duration) * 100}%` : '0%' }}></div>
              </div>
              <span className="timeInfo">{formatTime(currentTime)} / {formatTime(duration)}</span>
            </div>
          </div>
        </div>

        <div className="videoInfoSection">
          <div className="videoInfo">
            <h2>{videoData.filename}</h2>
            <div className="infoGrid">
              <div className="infoItem">
                <label>생성 일시:</label>
                <span>{formatDate(videoData.createdAt)}</span>
              </div>
              <div className="infoItem">
                <label>파일 크기:</label>
                <span>{getFileSize()}</span>
              </div>
              <div className="infoItem">
                <label>영상 길이:</label>
                <span>{duration > 0 ? formatTime(duration) : '로드 중...'}</span>
              </div>
              <div className="infoItem">
                <label>영상 ID:</label>
                <span>{videoData.id}</span>
              </div>
            </div>

            {debugInfo && (
              <div style={{
                marginTop: '15px',
                padding: '10px',
                backgroundColor: '#f5f5f5',
                borderRadius: '4px',
                fontSize: '11px',
                fontFamily: 'monospace',
                wordBreak: 'break-all'
              }}>
                <strong>디버그 정보:</strong><br/>
                {debugInfo}
              </div>
            )}

            <div className="checkStatusSection">
              <div className="statusInfo">
                <label>확인 상태:</label>
                <div className={videoData.isChecked ? "statusBadge checked" : "statusBadge unchecked"}>
                  {videoData.isChecked ? "✓ 확인 완료" : "⏳ 확인 대기"}
                </div>
              </div>
              <button className={`toggleCheckBtn ${videoData.isChecked ? "checked" : "unchecked"}`} onClick={handleToggleCheck}>
                {videoData.isChecked ? "미확인으로 변경" : "확인 완료로 변경"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CheckVideo;
