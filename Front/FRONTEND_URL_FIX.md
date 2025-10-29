# 🔗 프론트엔드 백엔드 URL 수정 완료

## ✅ 수정된 파일들

### 1. `src/App.jsx`
- 알림 폴링 API 호출 수정
- 테스트 함수들 수정
- 환경변수 사용하도록 변경

### 2. `src/hooks/DataContext.jsx`
- Mock 스트림 URL 수정
- 테스트 스트림 연결 URL 수정

### 3. `.env` 파일 (이미 생성됨)
```env
VITE_BACKEND_URL=http://43.203.245.90:8000
VITE_API_BASE_URL=http://43.203.245.90:8000/api
```

---

## 🚀 재배포 방법

```bash
cd Front

# 기존 빌드 삭제
rm -rf dist

# 재빌드
npm install
npm run build

# S3에 업로드
aws s3 sync dist/ s3://safefall2/ --delete

# 브라우저 캐시 삭제 후 테스트
# Chrome: Cmd + Shift + R (강력 새로고침)
```

---

## ✅ 테스트 방법

### 1. 브라우저에서 접속
```
http://safefall2.s3-website.ap-northeast-2.amazonaws.com
```

### 2. 개발자 도구 확인 (F12)
- **Console 탭**: `localhost` 에러가 없어야 함
- **Network 탭**: API 요청이 `43.203.245.90:8000`으로 가는지 확인

### 3. 정상 동작 확인
- 로그인 성공
- 대시보드 로드
- 알림 수신

---

## 📝 변경 내용 요약

**수정 전:**
```javascript
fetch('http://localhost:5000/api/...')
fetch('http://192.168.0.6:5000/...')
```

**수정 후:**
```javascript
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://43.203.245.90:8000';
fetch(`${BACKEND_URL}/api/...`)
```

---

**작업자:** 최현진  
**작업일:** 2025-10-20  
**상태:** ✅ 완료 - 재빌드 및 S3 배포 필요
