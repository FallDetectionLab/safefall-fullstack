# 🔐 JWT 토큰 401 UNAUTHORIZED 에러 해결!

## 📋 문제 상황

```
GET http://localhost:5001/api/incidents/list 401 (UNAUTHORIZED)
GET http://localhost:5001/api/dashboard/stats 401 (UNAUTHORIZED)
Failed to fetch videos: Request failed with status code 401
```

**원인**: 로그인은 성공했지만, 페이지 새로고침 시 localStorage의 JWT 토큰이 httpClient에 자동으로 복원되지 않음

---

## ✅ 해결 방법

### 수정한 파일: `Front/src/services/httpClient.js`

#### 1. 페이지 로드 시 토큰 자동 복원
```javascript
// 초기화: localStorage에서 토큰 로드
if (typeof window !== 'undefined') {
  authToken = localStorage.getItem('access_token');
  refreshToken = localStorage.getItem('refresh_token');
  
  if (authToken) {
    console.log('✅ [httpClient] Token restored from localStorage');
  }
}
```

#### 2. 토큰 설정 시 localStorage에 자동 저장
```javascript
setAuthToken(token) { 
  authToken = token;
  if (token && typeof window !== 'undefined') {
    localStorage.setItem('access_token', token);
    console.log('✅ [httpClient] Access token saved to localStorage');
  }
}
```

#### 3. 토큰 삭제 시 localStorage도 함께 삭제
```javascript
clearAuthTokens() { 
  authToken = null; 
  refreshToken = null;
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    console.log('🗑️ [httpClient] All tokens cleared');
  }
}
```

---

## 🚀 적용 방법

### 프론트엔드만 재시작 (백엔드는 그대로)

```bash
cd /Users/choihyunjin/poly/safefall-fullstack-main/Front

# 기존 프로세스 종료
lsof -ti:5173 | xargs kill -9
lsof -ti:5174 | xargs kill -9

# 다시 실행
npm run dev
```

---

## 🧪 테스트

### 1. 브라우저 개발자 도구 열기 (F12)

### 2. Console 탭에서 확인

프론트엔드 재시작 후 페이지 로드 시 다음 로그가 나타나야 함:
```
✅ [httpClient] Token restored from localStorage
```

로그인 시:
```
✅ [httpClient] Access token saved to localStorage
✅ [httpClient] Refresh token saved to localStorage
```

### 3. localStorage 확인

Console에서 실행:
```javascript
localStorage.getItem('access_token')
```

JWT 토큰이 출력되어야 함:
```
"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ..."
```

### 4. API 요청 확인

Network 탭 → 아무 API 요청 클릭 → Headers → Request Headers:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## ✅ 예상 결과

### Before (수정 전)
- ❌ 로그인 성공
- ❌ 페이지 새로고침 → 401 에러
- ❌ 모든 API 요청 실패
- ❌ 화면에 데이터 없음

### After (수정 후)
- ✅ 로그인 성공
- ✅ 페이지 새로고침 → 토큰 자동 복원
- ✅ 모든 API 요청 성공 (Authorization 헤더 포함)
- ✅ 화면에 데이터 정상 표시

---

## 🔍 추가 디버깅

### 여전히 401 에러가 나온다면?

#### 1. localStorage 수동 확인
```javascript
// Console에서 실행
console.log('Access Token:', localStorage.getItem('access_token'));
console.log('Refresh Token:', localStorage.getItem('refresh_token'));
```

#### 2. 토큰 만료 확인
JWT 토큰은 1시간 후 만료됩니다. 다시 로그인하세요:
```
로그아웃 → 로그인 (1 / admin123)
```

#### 3. 백엔드 로그 확인
백엔드 터미널에서 다음과 같은 로그가 나와야 함:
```
🌐 Incoming request: GET /api/incidents/list
   Remote addr: 127.0.0.1
```

#### 4. 완전히 초기화
```javascript
// Console에서 실행
localStorage.clear();
// 페이지 새로고침 → 다시 로그인
```

---

## 📝 작동 원리

### 로그인 플로우
```
1. 사용자 로그인 (1 / admin123)
   ↓
2. 백엔드에서 JWT 토큰 발급
   ↓
3. DataContext에서 토큰 받음
   ↓
4. httpClient.setAuthToken() 호출
   ↓
5. 🔥 FIX: localStorage에 자동 저장
   ↓
6. 이후 모든 API 요청에 Authorization 헤더 포함
```

### 페이지 새로고침 플로우
```
1. 브라우저 새로고침
   ↓
2. 🔥 FIX: httpClient 초기화 시 localStorage에서 토큰 로드
   ↓
3. authToken 변수에 토큰 복원
   ↓
4. 이후 모든 API 요청에 Authorization 헤더 포함
```

---

## 🎯 핵심 변경사항

1. **페이지 로드 시 자동 복원**: localStorage → authToken 변수
2. **토큰 설정 시 자동 저장**: authToken 변수 → localStorage
3. **토큰 삭제 시 완전 제거**: localStorage도 함께 삭제

이제 **로그인 상태가 페이지 새로고침 후에도 유지**됩니다! 🎉

---

생성일: 2025-10-21
