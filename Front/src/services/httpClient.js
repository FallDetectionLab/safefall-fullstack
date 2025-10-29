/**
 * 확장 HTTP 클라이언트:
 * - 5000 포트 강제
 * - Authorization 토큰 관리
 * - 간단 메모리 캐시 (GET)
 * - cacheTime(ms) 만료
 * - clearCache(pattern) 지원
 */

import axios from 'axios';

// Backend URL configuration - uses environment variable with fallback
// For Vite projects, use VITE_BACKEND_URL environment variable
// Fallback to Raspberry Pi backend address
const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://43.203.245.90:8000';

// 🔥 CRITICAL FIX: 페이지 로드 시 localStorage에서 토큰 자동 복원
let authToken = null;
let refreshToken = null;

// 초기화: localStorage에서 토큰 로드
if (typeof window !== 'undefined') {
  authToken = localStorage.getItem('access_token');
  refreshToken = localStorage.getItem('refresh_token');
  
  if (authToken) {
    console.log('✅ [httpClient] Token restored from localStorage');
  } else {
    console.log('ℹ️ [httpClient] No token found in localStorage');
  }
}

const cacheStore = new Map(); // key: METHOD|URL -> { expire:number, data:any }
const now = () => Date.now();

const instance = axios.create({
  baseURL: BASE_URL,
  timeout: 10000
});

// 요청 인터셉터
instance.interceptors.request.use(cfg => {
  cfg.baseURL = BASE_URL;
  if (authToken) {
    cfg.headers = cfg.headers || {};
    cfg.headers.Authorization = `Bearer ${authToken}`;
  }
  return cfg;
});

// 응답 인터셉터 (에러시 단순 전달)
instance.interceptors.response.use(
  res => res,
  err => Promise.reject(err)
);

// 내부: 캐시 키 생성
const makeKey = (method, url, paramsKey='') => `${method}|${url}|${paramsKey}`;

// 공개 메소드
const httpClient = {
  setAuthToken(token) { 
    authToken = token;
    // 🔥 CRITICAL FIX: localStorage에도 자동 저장
    if (token && typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
      console.log('✅ [httpClient] Access token saved to localStorage');
    } else if (!token && typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      console.log('🗑️ [httpClient] Access token removed from localStorage');
    }
  },
  setRefreshToken(token) { 
    refreshToken = token;
    // 🔥 CRITICAL FIX: localStorage에도 자동 저장
    if (token && typeof window !== 'undefined') {
      localStorage.setItem('refresh_token', token);
      console.log('✅ [httpClient] Refresh token saved to localStorage');
    } else if (!token && typeof window !== 'undefined') {
      localStorage.removeItem('refresh_token');
      console.log('🗑️ [httpClient] Refresh token removed from localStorage');
    }
  },
  clearAuthTokens() { 
    authToken = null; 
    refreshToken = null;
    // 🔥 CRITICAL FIX: localStorage에서도 제거
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      console.log('🗑️ [httpClient] All tokens cleared');
    }
  },
  getRefreshToken() { return refreshToken; },

  clearCache(pattern) {
    if (!pattern) {
      cacheStore.clear();
      return;
    }
    const regex = new RegExp(pattern);
    for (const k of [...cacheStore.keys()]) {
      if (regex.test(k)) cacheStore.delete(k);
    }
  },

  // GET (options: { cache:boolean, cacheTime:number, timeoutMs:number })
  async get(url, options = {}) {
    const { cache = false, cacheTime = 0, timeoutMs, params } = options;
    const paramsKey = params ? JSON.stringify(params) : '';
    const key = makeKey('GET', url, paramsKey);

    if (cache) {
      const hit = cacheStore.get(key);
      if (hit && hit.expire > now()) {
        return hit.data;
      } else if (hit) {
        cacheStore.delete(key);
      }
    }

    const controller = timeoutMs ? new AbortController() : null;
    if (controller) setTimeout(() => controller.abort(), timeoutMs);

    const res = await instance.get(url, {
      params,
      signal: controller?.signal
    }).then(r => r.data);

    if (cache && cacheTime > 0) {
      cacheStore.set(key, { expire: now() + cacheTime, data: res });
    }
    return res;
  },

  async post(url, data = {}, options = {}) {
    const { timeoutMs } = options;
    const controller = timeoutMs ? new AbortController() : null;
    if (controller) setTimeout(() => controller.abort(), timeoutMs);
    return instance.post(url, data, { signal: controller?.signal }).then(r => r.data);
  },

  async put(url, data = {}, options = {}) {
    return instance.put(url, data).then(r => r.data);
  },

  async patch(url, data = {}, options = {}) {
    return instance.patch(url, data).then(r => r.data);
  },

  async delete(url, options = {}) {
    return instance.delete(url).then(r => r.data);
  }
};

export default httpClient;