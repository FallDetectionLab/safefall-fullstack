/**
 * 영상 기록 목록 페이지 컴포넌트
 * - 전체 낙상 감지 영상 목록 표시
 * - 페이지네이션 기능
 * - 확인 여부 필터링 및 정렬
 * - 영상 클릭 시 CheckVideo 페이지로 이동
 * - 실시간 데이터 새로고침 지원
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";

import WindowSize from "../hooks/windowSize";
import VideoBtnSmall from "../components/SVG-VideoBtnSmall";

import * as apiService from "../services/api"; // ← (선택) 서버 사전검증용
import "./CheckHistory.css";

function CheckHistory({
  incidentVideos = [],
  updateVideoCheckStatus,
  deleteIncidentVideo,
  getFilteredVideos,
  videoFilters,
  updateFilters,
  resetFilters,
  getVideoStats,
  refreshIncidentVideos,  // 🔥 데이터 새로고침 함수 추가
}) {
  const { width } = WindowSize();
  const navigate = useNavigate();

  // 페이지네이션
  const [currentPage, setCurrentPage] = useState(1);

  // 클릭/에러 상태
  const [clickingKey, setClickingKey] = useState(null); // id 또는 filename으로 식별
  const [errorMsg, setErrorMsg] = useState("");
  
  // 🔧 임시 수정된 영상 데이터 사용
  const getDisplayVideos = () => {
    // 브라우저 전역 변수에서 수정된 데이터 우선 사용
    if (window.safeFallFixedVideos && window.safeFallFixedVideos.length > 0) {
      console.log('🔧 수정된 영상 데이터 사용:', window.safeFallFixedVideos.length, '개');
      return window.safeFallFixedVideos;
    }
    
    // MP4 파일만 필터링
    const mp4Videos = incidentVideos.filter(video => 
      video.filename && 
      (video.filename.endsWith('.mp4') || video.path?.includes('.mp4'))
    );
    
    if (mp4Videos.length > 0) {
      console.log('🎬 MP4 영상만 표시:', mp4Videos.length, '개');
      return mp4Videos;
    }
    
    // 기본 데이터 사용
    return incidentVideos;
  };

  // 화면 크기에 따른 페이지당 아이템 수
  const itemsPerPage = width >= 1200 ? 8 : 6;

  // 총 페이지 수 (필터링된 영상 수 기준) - 임시로 전체 영상 사용
  const totalPages = useMemo(() => {
    // 🔧 임시: 전체 영상 사용
    const totalCount = incidentVideos?.length || 0;
    return Math.ceil(totalCount / itemsPerPage);
  }, [incidentVideos, itemsPerPage]);

  // (성능) 모든 파일 표시하고 정렬된 메모 - MP4 필터 임시 해제
  const sortedVideos = useMemo(() => {
    // 🔧 임시: MP4 필터링 해제하고 모든 영상 표시
    const allVideos = incidentVideos ?? [];
    
    console.log(`🎬 영상 표시: 전체 ${allVideos.length}개 표시 (MP4 필터 해제)`);
    console.log('영상 데이터 샘플:', allVideos.slice(0, 3));
    
    return allVideos
      .slice()
      .sort((a, b) => {
        const tb = Date.parse(b?.createdAt ?? 0) || 0;
        const ta = Date.parse(a?.createdAt ?? 0) || 0;
        return tb - ta; // 최신순
      });
  }, [incidentVideos]);

  // ✅ PERFORMANCE FIX: 현재 페이지 데이터 메모이제이션
  // 페이지나 아이템 수가 변경되지 않으면 재계산하지 않음
  const currentPageData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return sortedVideos.slice(startIndex, endIndex);
  }, [currentPage, itemsPerPage, sortedVideos]);

  // 페이지 이동
  const goToPage = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber);
    }
  };
  const goToPrevPage = () => currentPage > 1 && setCurrentPage(currentPage - 1);
  const goToNextPage = () =>
    currentPage < totalPages && setCurrentPage(currentPage + 1);

  // 화면 크기/데이터 변경 시 페이지 보정
  useEffect(() => {
    const newTotalPages = Math.ceil((incidentVideos?.length ?? 0) / itemsPerPage);
    if (currentPage > newTotalPages && newTotalPages > 0) {
      setCurrentPage(newTotalPages);
    }
  }, [width, incidentVideos?.length, itemsPerPage, currentPage]);
  
  // 🔥 컴포넌트 마운트 시 데이터 새로고침
  useEffect(() => {
    console.log('📜 CheckHistory 컴포넌트 마운트 - 데이터 새로고침 시도');
    
    if (refreshIncidentVideos) {
      refreshIncidentVideos()
        .then(() => {
          console.log('✅ CheckHistory 마운트 시 데이터 새로고침 완료');
        })
        .catch((error) => {
          console.error('❌ CheckHistory 마운트 시 데이터 새로고침 실패:', error);
        });
    }
  }, [refreshIncidentVideos]); // ✅ FIX: refreshIncidentVideos 의존성 추가

  // 날짜 포맷팅
  const formatDate = (dateString) => {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return "날짜 정보 없음";
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${year} / ${month} / ${day}`;
  };

  // (선택) 서버에 존재하는지 확인하는 보조 함수
  const checkVideoExists = async ({ id, filename }) => {
    // apiService에 대응 메서드가 있는 경우에만 시도 (duck-typing)
    try {
      if (id && typeof apiService?.getVideoById === "function") {
        const res = await apiService.getVideoById(id);
        return !!res?.data;
      }
      if (filename && typeof apiService?.getVideoMetaByFilename === "function") {
        const res = await apiService.getVideoMetaByFilename(filename);
        return !!res?.data;
      }
      // 메서드가 없다면 서버 사전검증은 생략하고 프론트 단으로 통과
      return true;
    } catch {
      return false; // 404/에러 → 존재하지 않음 처리
    }
  };

  // 영상 클릭(사전 검증 + 이동)
  const handleVideoClick = async (item) => {
    try {
      setErrorMsg("");

      // 연속 클릭 방지
      if (clickingKey) return;

      // 필수 키 검사 (id 또는 filename 중 하나는 필요)
      const key = item?.id ?? item?.filename;
      if (!key) {
        throw new Error("NO_KEY");
      }
      setClickingKey(key);

      console.log('영상 클릭:', item);
      console.log('ID:', item?.id, 'Filename:', item?.filename);

      // ID가 숫자인 경우와 파일명인 경우를 구분
      let target;
      if (item?.id && typeof item.id === 'number') {
        // 숫자 ID가 있는 경우
        target = `/video/${item.id}`;
        console.log('ID로 라우팅:', target);
      } else if (item?.filename) {
        // 파일명으로 라우팅
        target = `/video/${encodeURIComponent(String(item.filename))}`;
        console.log('파일명으로 라우팅:', target);
      } else {
        throw new Error("NO_VALID_IDENTIFIER");
      }

      navigate(target);
    } catch (e) {
      console.error('영상 클릭 오류:', e);
      // 공통 에러 메시지
      setErrorMsg(
        "영상을 찾을 수 없습니다\n요청하신 영상이 존재하지 않거나 삭제되었습니다."
      );
    } finally {
      setClickingKey(null);
    }
  };

  // 키보드 접근(Enter/Space)
  const onItemKeyDown = (e, item) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleVideoClick(item);
    }
  };

  return (
    <div className="CheckHistorySection">
      {/* 에러 배너 */}
      {errorMsg && (
        <div className="historyError" role="alert" aria-live="assertive">
          {errorMsg.split("\n").map((line, i) => (
            <p key={i}>{line}</p>
          ))}
        </div>
      )}
      
      {/* 영상 정보 */}
      <div className="syncSection" style={{
        display: 'flex',
        justifyContent: 'flex-start',
        alignItems: 'center',
        marginBottom: '20px',
        padding: '10px',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #e9ecef'
      }}>
        <div>
          <h3 style={{margin: '0 0 5px 0', fontSize: '16px'}}>영상 목록</h3>
          <p style={{margin: 0, fontSize: '14px', color: '#6c757d'}}>
            전체 영상 {sortedVideos?.length || 0}개
          </p>
        </div>
      </div>

      <div className="historyListBox">
        <ul className="historyLost">
          {currentPageData.map((item, index) => {
            const rowKey = `${item?.id ?? item?.filename ?? "unknown"}-${item?.createdAt ?? index}-${index}`;
            const disabled = clickingKey && clickingKey === (item?.id ?? item?.filename);

            return (
              <li
                key={rowKey}
                onClick={() => handleVideoClick(item)}
                onKeyDown={(e) => onItemKeyDown(e, item)}
                role="button"
                tabIndex={0}
                aria-disabled={disabled ? "true" : "false"}
                style={{
                  cursor: disabled ? "not-allowed" : "pointer",
                  opacity: disabled ? 0.6 : 1,
                }}
              >
                <div className="historyThumnail">
                  <VideoBtnSmall />
                </div>
                <div className="historyinfo">
                  <h3 className="historyFilename">
                    {item?.filename ?? "(파일명 없음)"}
                  </h3>
                  <div className="historyDetailBox">
                    <p className="historycreatedAt">
                      {formatDate(item?.createdAt)}
                    </p>
                    <div className="historyCheckbox">
                      <p>확인 여부</p>
                      <div
                        className={
                          item?.isChecked
                            ? "checkBoxSmall checkFinish"
                            : "checkBoxSmall checkPrev"
                        }
                      >
                        {item?.isChecked ? "완료" : "대기"}
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="historyListBoxBtn">
          <div className="pagination">
            <button
              className={`pagination-arrow ${currentPage === 1 ? "disabled" : ""}`}
              onClick={goToPrevPage}
              disabled={currentPage === 1}
            >
              &#8249;
            </button>

            <div className="pagination-numbers">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                (pageNumber) => (
                  <button
                    key={pageNumber}
                    className={`pagination-number ${
                      currentPage === pageNumber ? "active" : ""
                    }`}
                    onClick={() => goToPage(pageNumber)}
                  >
                    {pageNumber}
                  </button>
                )
              )}
            </div>

            <button
              className={`pagination-arrow ${
                currentPage === totalPages ? "disabled" : ""
              }`}
              onClick={goToNextPage}
              disabled={currentPage === totalPages}
            >
              &#8250;
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default CheckHistory;
