@echo off
REM SafeFall 빠른 배포 스크립트 (Windows)

echo 🚀 SafeFall 배포를 시작합니다...

REM 1. 환경 변수 확인
if not exist .env (
    echo ⚠️  .env 파일이 없습니다. .env.example을 복사합니다...
    copy .env.example .env
    echo ✅ .env 파일이 생성되었습니다. 파일을 수정한 후 다시 실행해주세요.
    pause
    exit /b 1
)

REM 2. Frontend 환경 변수 확인
if not exist Front\.env (
    echo ⚠️  Front\.env 파일이 없습니다.
    set /p backend_url="Backend 서버 주소를 입력하세요 (예: http://localhost:5000): "
    echo VITE_BACKEND_URL=%backend_url% > Front\.env
    echo ✅ Front\.env 파일이 생성되었습니다.
)

REM 3. Docker 설치 확인
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker가 설치되어 있지 않습니다.
    echo Docker Desktop을 설치한 후 다시 시도해주세요: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose가 설치되어 있지 않습니다.
    pause
    exit /b 1
)

REM 4. 이전 컨테이너 정리
echo 🧹 이전 컨테이너를 정리합니다...
docker-compose down

REM 5. 이미지 빌드
echo 🔨 Docker 이미지를 빌드합니다...
docker-compose build

REM 6. 컨테이너 실행
echo ▶️  컨테이너를 실행합니다...
docker-compose up -d

REM 7. 상태 확인
echo ✅ 배포가 완료되었습니다!
echo.
echo 📊 컨테이너 상태:
docker-compose ps

echo.
echo 🌐 접속 정보:
echo    Frontend: http://localhost
echo    Backend:  http://localhost:5000
echo.
echo 📝 로그 확인: docker-compose logs -f
echo 🛑 중지: docker-compose down

pause
