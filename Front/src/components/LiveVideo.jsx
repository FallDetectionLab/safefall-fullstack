/**
 * 실시간 영상 스트리밍 컴포넌트
 * - MJPEG 스트리밍 및 스냅샷 폴백 지원
 * - 3가지 모드: MJPEG Primary, MJPEG Fallback, Snapshot
 * - 스트림 실패 시 자동 폴백 처리
 * - 디버그 모드 지원
 * - 404 에러 감지 및 exponential backoff 적용
 */
import React, { useEffect, useMemo, useRef, useState } from "react";
import { getBackendBaseUrl, joinUrl } from "../utils/backendUrls";

const SNAPSHOT_INTERVAL_MS = 800;
const STALE_THRESHOLD_MS = 6000;
const STALE_CHECK_MS = 2000;
const SNAPSHOT_BACKOFF_MAX_MS = 10000;
const SNAPSHOT_BACKOFF_GROWTH = 2;
const MAX_CONSECUTIVE_404S = 5;

export default function LiveVideo({ config }) {
  const backendBase = useMemo(
    () => getBackendBaseUrl(config?.backendBase),
    [config?.backendBase]
  );

  const mjpegPrimaryUrl = useMemo(
    () => joinUrl(backendBase, "api/stream/mjpeg"),
    [backendBase]
  );
  const mjpegFallbackUrl = useMemo(
    () => joinUrl(backendBase, "api/stream/mjpeg"),
    [backendBase]
  );
  const snapshotUrl = useMemo(
    () => joinUrl(backendBase, "api/frame/latest"),
    [backendBase]
  );
  const detectMetricsUrl = useMemo(
    () => joinUrl(backendBase, "api/detect/metrics"),
    [backendBase]
  );

  const forceFallback = config?.forceFallback ||
    (typeof window !== "undefined" && window.__SAFEFALL_FORCE_FALLBACK__ === true);
  const debug = typeof window !== "undefined" && window.location.search.includes("debugStream=1");
  const detectDebug = typeof window !== "undefined" && window.location.search.includes("debugDetect=1");

  const imgRef = useRef(null);
  const abortRef = useRef(null);
  const backoffRef = useRef(SNAPSHOT_INTERVAL_MS);
  const consecutive404sRef = useRef(0);
  const consecutiveErrorsRef = useRef(0);

  const [mode, setMode] = useState(forceFallback ? "fallback" : "mjpeg");
  const [tick, setTick] = useState(() => Date.now());
  const [errorType, setErrorType] = useState(null);
  const [httpErrorCode, setHttpErrorCode] = useState(null);
  const [retry, setRetry] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [lastFrameTs, setLastFrameTs] = useState(null);
  const [stopped, setStopped] = useState(false);

  const mjpegSrc = useMemo(() => {
    if (mode === "mjpeg") {
      return `${mjpegPrimaryUrl}?_=${tick}`;
    }
    if (mode === "fallback") {
      return `${mjpegFallbackUrl}?_=${tick}`;
    }
    return "";
  }, [mode, tick, mjpegPrimaryUrl, mjpegFallbackUrl]);

  useEffect(() => {
    setMode(forceFallback ? "fallback" : "mjpeg");
    setIsLoading(true);
    setStopped(false);
    consecutive404sRef.current = 0;
    consecutiveErrorsRef.current = 0;
    backoffRef.current = SNAPSHOT_INTERVAL_MS;
    setHttpErrorCode(null);
    setErrorType(null);
  }, [forceFallback, backendBase]);

  useEffect(() => {
    if (mode !== "snapshot") {
      return undefined;
    }

    if (stopped) {
      return undefined;
    }

    let cancelled = false;

    const pullSnapshot = async () => {
      if (stopped || cancelled) {
        return;
      }

      try {
        const response = await fetch(snapshotUrl, { cache: "no-store" });

        // Handle 204 No Content (success but no frame available yet)
        if (response.status === 204) {
          // Reset error counters - this is a valid state
          if (consecutive404sRef.current > 0 || consecutiveErrorsRef.current > 0) {
            console.log('[LiveVideo] 204 No Content - 서버 정상, 프레임 대기 중');
            consecutive404sRef.current = 0;
            consecutiveErrorsRef.current = 0;
            backoffRef.current = SNAPSHOT_INTERVAL_MS;
          }
          setErrorType(null);
          setHttpErrorCode(null);
          scheduleNextPull();
          return;
        }

        // Always log HTTP errors, not just in debug mode
        if (!response.ok) {
          const status = response.status;
          console.error(
            `[LiveVideo] 스냅샷 요청 실패 - HTTP ${status}`,
            `(연속 실패: ${consecutiveErrorsRef.current + 1}회)`
          );

          consecutiveErrorsRef.current += 1;

          // Track 404 errors specifically
          if (status === 404) {
            consecutive404sRef.current += 1;
            console.error(
              `[LiveVideo] 404 Not Found - 엔드포인트를 찾을 수 없음`,
              `(연속 404: ${consecutive404sRef.current}회)`
            );

            // Stop after MAX_CONSECUTIVE_404S
            if (consecutive404sRef.current >= MAX_CONSECUTIVE_404S) {
              console.error(
                `[LiveVideo] ${MAX_CONSECUTIVE_404S}회 연속 404 에러 발생 - 재시도 중단`
              );
              setStopped(true);
              setErrorType("404");
              setHttpErrorCode(404);
              return;
            }
          }

          // Set appropriate error type based on status code
          if (status === 404) {
            setErrorType("404");
            setHttpErrorCode(404);
          } else if (status >= 500) {
            setErrorType("server_error");
            setHttpErrorCode(status);
          } else {
            setErrorType("http_error");
            setHttpErrorCode(status);
          }

          // Implement exponential backoff
          const nextBackoff = Math.min(
            backoffRef.current * SNAPSHOT_BACKOFF_GROWTH,
            SNAPSHOT_BACKOFF_MAX_MS
          );

          if (debug) {
            console.log(
              `[LiveVideo] 다음 재시도까지 대기: ${nextBackoff}ms`,
              `(현재 backoff: ${backoffRef.current}ms)`
            );
          }

          backoffRef.current = nextBackoff;
          scheduleNextPull();
          return;
        }

        // Success - reset error counters and backoff
        if (consecutive404sRef.current > 0 || consecutiveErrorsRef.current > 0) {
          console.log(
            `[LiveVideo] 스냅샷 요청 성공 - 에러 카운터 리셋`,
            `(이전 연속 에러: ${consecutiveErrorsRef.current}회, 404: ${consecutive404sRef.current}회)`
          );
        }

        consecutive404sRef.current = 0;
        consecutiveErrorsRef.current = 0;
        backoffRef.current = SNAPSHOT_INTERVAL_MS;
        setErrorType(null);
        setHttpErrorCode(null);

        const blob = await response.blob();

        // Validate frame size
        if (blob.size <= 130) {
          if (debug) {
            console.warn(
              `[LiveVideo] 프레임 크기가 너무 작음 (${blob.size} bytes) - 무시`
            );
          }
          return;
        }

        setLastFrameTs(Date.now());

        const nextUrl = URL.createObjectURL(blob);
        if (imgRef.current && !cancelled) {
          imgRef.current.onload = () => URL.revokeObjectURL(nextUrl);
          imgRef.current.src = nextUrl;
        }

        if (!cancelled) {
          setIsLoading(false);
        }

        scheduleNextPull();
      } catch (error) {
        consecutiveErrorsRef.current += 1;

        // Always log network errors
        console.error(
          `[LiveVideo] 네트워크 에러 발생 - ${error.message}`,
          `(연속 실패: ${consecutiveErrorsRef.current}회)`
        );

        setErrorType("network_error");
        setHttpErrorCode(null);

        // Implement exponential backoff for network errors too
        const nextBackoff = Math.min(
          backoffRef.current * SNAPSHOT_BACKOFF_GROWTH,
          SNAPSHOT_BACKOFF_MAX_MS
        );
        backoffRef.current = nextBackoff;

        if (debug) {
          console.warn("[LiveVideo] snapshot fetch failed", error);
        }

        scheduleNextPull();
      }
    };

    // Dynamic retry scheduling using setTimeout
    let timeoutId = null;

    const scheduleNextPull = () => {
      if (stopped || cancelled) return;

      timeoutId = setTimeout(() => {
        pullSnapshot();
      }, backoffRef.current);
    };

    // Initial call
    pullSnapshot();

    return () => {
      cancelled = true;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [mode, snapshotUrl, debug, stopped]);

  useEffect(() => {
    if (mode === "snapshot") {
      return undefined;
    }

    const timer = setInterval(() => {
      if (!imgRef.current || !lastFrameTs) {
        return;
      }
      if (Date.now() - lastFrameTs > STALE_THRESHOLD_MS) {
        if (debug) {
          console.warn("[LiveVideo] stream stale, switching to snapshot");
        }
        setMode("snapshot");
      }
    }, STALE_CHECK_MS);

    return () => clearInterval(timer);
  }, [mode, lastFrameTs, debug]);

  const preflightCheck = async (url) => {
    try {
      const controller = new AbortController();
      abortRef.current = controller;
      const response = await fetch(url, {
        method: "GET",
        signal: controller.signal,
        cache: "no-store",
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  };

  useEffect(() => {
    if (forceFallback && mode === "fallback") {
      return undefined;
    }
    if (mode !== "mjpeg" && mode !== "fallback") {
      return undefined;
    }

    let cancelled = false;
    const target = mode === "mjpeg" ? mjpegPrimaryUrl : mjpegFallbackUrl;

    (async () => {
      const ok = await preflightCheck(`${target}?preflight=${Date.now()}`);
      if (cancelled) {
        return;
      }
      if (!ok) {
        if (mode === "mjpeg") {
          setMode("fallback");
          setIsLoading(true);
          setErrorType("refused");
          setTick(Date.now());
        } else {
          setMode("snapshot");
          setIsLoading(true);
          setErrorType("refused");
        }
      } else {
        setTick(Date.now());
        setErrorType(null);
        setHttpErrorCode(null);
      }
    })();

    return () => {
      cancelled = true;
      if (abortRef.current) {
        abortRef.current.abort();
        abortRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, mjpegPrimaryUrl, mjpegFallbackUrl, forceFallback]);

  const handleLoad = () => {
    try {
      if (
        imgRef.current &&
        (imgRef.current.naturalWidth <= 2 || imgRef.current.naturalHeight <= 2)
      ) {
        if (debug) {
          console.log("[LiveVideo] placeholder frame ignored");
        }
        setTimeout(() => setTick(Date.now()), 400);
        return;
      }
    } catch (error) {
      if (debug) {
        console.warn("[LiveVideo] load check error", error);
      }
    }

    setLastFrameTs(Date.now());
    setIsLoading(false);
    setErrorType(null);
    setHttpErrorCode(null);
    if (debug) {
      console.log("[LiveVideo] frame loaded", mode, backendBase);
    }
    backoffRef.current = SNAPSHOT_INTERVAL_MS;
    consecutive404sRef.current = 0;
    consecutiveErrorsRef.current = 0;
  };

  const handleError = () => {
    if (debug) {
      console.warn("[LiveVideo] load error", mode, "retry", retry);
    }

    setIsLoading(true);
    setRetry((prev) => prev + 1);

    if (mode === "mjpeg") {
      setErrorType("refused");
      setMode("fallback");
      setTick(Date.now());
      return;
    }

    if (mode === "fallback") {
      setErrorType("refused");
      setMode("snapshot");
      return;
    }

    setTimeout(() => setTick(Date.now()), backoffRef.current);
    backoffRef.current = Math.min(
      backoffRef.current * SNAPSHOT_BACKOFF_GROWTH,
      SNAPSHOT_BACKOFF_MAX_MS
    );
  };

  const getErrorMessage = () => {
    if (stopped && errorType === "404") {
      return {
        title: "엔드포인트를 찾을 수 없음 (404)",
        subtitle: `${MAX_CONSECUTIVE_404S}회 연속 실패 - 재시도 중단됨`,
        color: "#ff4444"
      };
    }

    if (errorType === "404") {
      return {
        title: "엔드포인트를 찾을 수 없음 (404)",
        subtitle: `재시도 중... (${consecutive404sRef.current}/${MAX_CONSECUTIVE_404S})`,
        color: "#ff9944"
      };
    }

    if (errorType === "server_error") {
      return {
        title: `서버 에러 (${httpErrorCode})`,
        subtitle: "서버에 문제가 발생했습니다",
        color: "#ff6666"
      };
    }

    if (errorType === "http_error") {
      return {
        title: `HTTP 에러 (${httpErrorCode})`,
        subtitle: "요청 처리 중 문제가 발생했습니다",
        color: "#ff8866"
      };
    }

    if (errorType === "network_error") {
      return {
        title: "연결 실패",
        subtitle: "네트워크 연결을 확인해주세요",
        color: "#ff6666"
      };
    }

    if (errorType === "refused") {
      return {
        title: mode === "snapshot"
          ? "스트림 오프라인 - 스냅샷 모드"
          : "기본 스트림 연결 실패 - 폴백 시도 중",
        subtitle: null,
        color: "#ffaa44"
      };
    }

    return null;
  };

  const renderOverlay = () => {
    const errorMsg = getErrorMessage();

    if (!isLoading && !errorMsg) {
      return null;
    }

    if (mode === "snapshot" && !isLoading && !errorMsg) {
      return null;
    }

    let displayMessage = "스트림 로딩 중...";
    let messageColor = "#666";
    let subtitle = null;

    if (errorMsg) {
      displayMessage = errorMsg.title;
      messageColor = errorMsg.color;
      subtitle = errorMsg.subtitle;
    } else if (mode === "fallback") {
      displayMessage = "폴백 스트림 연결 중...";
    }

    return (
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 2,
          color: messageColor,
          fontSize: 14,
          fontWeight: errorMsg ? 600 : 400,
          textAlign: "center",
          whiteSpace: "pre-line",
        }}
      >
        {displayMessage}
        {subtitle && (
          <div style={{ marginTop: 8, fontSize: 12, opacity: 0.9 }}>
            {subtitle}
          </div>
        )}
        <div style={{ marginTop: 6, fontSize: 11, opacity: 0.7, fontWeight: 400 }}>
          {backendBase}
        </div>
        {stopped && (
          <div style={{ marginTop: 12, fontSize: 12, color: "#aaa" }}>
            페이지를 새로고침하여 다시 시도하세요
          </div>
        )}
      </div>
    );
  };

  useEffect(() => {
    if (!detectDebug) {
      return undefined;
    }
    const id = setInterval(async () => {
      try {
        const payload = await fetch(detectMetricsUrl, { cache: "no-store" }).then((r) => r.json());
        console.log("[DetectMetrics]", payload);
      } catch (error) {
        console.warn("[DetectMetrics] error", error);
      }
    }, 5000);
    return () => clearInterval(id);
  }, [detectDebug, detectMetricsUrl]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      {renderOverlay()}
      {mode !== "snapshot" && (
        <img
          ref={imgRef}
          src={mjpegSrc}
          alt="Live Stream"
          onLoad={handleLoad}
          onError={handleError}
          style={{
            display: "block",
            width: "100%",
            height: "auto",
            borderRadius: 8,
            background: "#000",
            opacity: isLoading ? 0.55 : 1,
            transition: "opacity .25s",
          }}
        />
      )}
      {mode === "snapshot" && (
        <img
          ref={imgRef}
          alt="Live Snapshot"
          style={{
            display: "block",
            width: "100%",
            height: "auto",
            borderRadius: 8,
            background: "#000",
            opacity: isLoading ? 0.55 : 1,
            transition: "opacity .25s",
          }}
        />
      )}
      {debug && (
        <div
          style={{
            position: "absolute",
            left: 8,
            bottom: 8,
            background: "rgba(0,0,0,0.55)",
            color: "#0f0",
            fontSize: 10,
            padding: "4px 6px",
            borderRadius: 4,
            lineHeight: 1.3,
          }}
        >
          <div>mode: {mode}</div>
          <div>forceFallback: {String(forceFallback)}</div>
          <div>retry: {retry}</div>
          <div>last: {lastFrameTs ? ((Date.now() - lastFrameTs) / 1000).toFixed(1) + "s" : "-"}</div>
          <div>err: {errorType || "none"}</div>
          <div>http: {httpErrorCode || "none"}</div>
          <div>404s: {consecutive404sRef.current}</div>
          <div>errors: {consecutiveErrorsRef.current}</div>
          <div>backoff: {backoffRef.current}ms</div>
          <div>stopped: {String(stopped)}</div>
          <div>base: {backendBase}</div>
        </div>
      )}
    </div>
  );
}
