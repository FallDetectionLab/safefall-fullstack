/**
 * 백엔드 URL 관리 유틸리티
 * - 환경 변수 및 전역 변수에서 백엔드 URL 자동 감지
 * - URL 정규화 및 조합 유틸리티 함수 제공
 * - API Base URL과 Backend Base URL 구분 관리
 */

const trimTrailingSlash = (value = '') => value.replace(/\/+$/, '');
const trimLeadingSlash = (value = '') => value.replace(/^\/+/, '');
const dropApiSuffix = (value = '') => value.replace(/\/api(?:\/v[0-9]+)?\/?$/i, '');

const ENV = import.meta.env || {};

const joinUrlInternal = (base, path = '') => {
  const normalizedBase = trimTrailingSlash(base || '');
  const normalizedPath = trimLeadingSlash(path || '');
  if (!normalizedPath) {
    return normalizedBase;
  }
  if (!normalizedBase) {
    return `/${normalizedPath}`;
  }
  return `${normalizedBase}/${normalizedPath}`;
};

const normalizeLocalhost = (value) => {
  try {
    const url = new URL(value);
    const isLocalhost = ['localhost', '127.0.0.1', '::1'].includes(url.hostname);
    if (!isLocalhost) {
      return trimTrailingSlash(url.toString());
    }

    url.port = '5000';
    return trimTrailingSlash(url.toString());
  } catch (error) {
    return trimTrailingSlash(value);
  }
};

export const joinUrl = (base, path = '') => joinUrlInternal(base, path);

export const getBackendBaseUrl = (preferred) => {
  if (preferred && typeof preferred === 'string' && preferred.trim()) {
    return trimTrailingSlash(preferred.trim());
  }

  if (typeof window !== 'undefined' && window.__SAFEFALL_BACKEND__) {
    return trimTrailingSlash(String(window.__SAFEFALL_BACKEND__));
  }

  if (ENV.VITE_BACKEND_URL) {
    return trimTrailingSlash(ENV.VITE_BACKEND_URL);
  }

  if (ENV.VITE_API_BASE_URL) {
    const base = dropApiSuffix(ENV.VITE_API_BASE_URL);
    return normalizeLocalhost(base);
  }

  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:5000`;
  }

  return 'http://localhost:5000';
};

export const getApiBaseUrl = (preferred) => {
  if (preferred && typeof preferred === 'string' && preferred.trim()) {
    return trimTrailingSlash(preferred.trim());
  }

  if (typeof window !== 'undefined' && window.__SAFEFALL_API_BASE__) {
    return trimTrailingSlash(String(window.__SAFEFALL_API_BASE__));
  }

  if (ENV.VITE_API_BASE_URL) {
    return trimTrailingSlash(ENV.VITE_API_BASE_URL);
  }

  return joinUrlInternal(getBackendBaseUrl(preferred), 'api');
};
