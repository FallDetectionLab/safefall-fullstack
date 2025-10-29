# 🔧 SafeFall 가상환경 설정 가이드

## 백엔드 가상환경 설정

### Windows 환경

```powershell
# 1. Back 디렉토리로 이동
cd E:\safefallFullstack-main\Back

# 2. 가상환경 생성
python -m venv venv

# 3. 가상환경 활성화
venv\Scripts\activate

# 4. pip 업그레이드
python -m pip install --upgrade pip

# 5. 의존성 설치
pip install -r requirements.txt

# 6. 기본 사용자 생성
python init_default_user.py

# 7. 서버 실행
python app.py
```

### Linux/Mac 환경

```bash
# 1. Back 디렉토리로 이동
cd ~/safefallFullstack-main/Back

# 2. 가상환경 생성
python3 -m venv venv

# 3. 가상환경 활성화
source venv/bin/activate

# 4. pip 업그레이드
pip install --upgrade pip

# 5. 의존성 설치
pip install -r requirements.txt

# 6. 기본 사용자 생성
python init_default_user.py

# 7. 서버 실행
python app.py
```

---

## 라즈베리파이 환경 설정

### 라즈베리파이 OS에서

```bash
# 1. RASP 디렉토리로 이동
cd ~/safefallFullstack-main/RASP

# 2. 가상환경 생성 (선택사항, 권장)
python3 -m venv venv

# 3. 가상환경 활성화 (가상환경 사용 시)
source venv/bin/activate

# 4. 시스템 패키지 업데이트
sudo apt update
sudo apt install -y python3-opencv

# 5. 의존성 설치
pip install ultralytics
pip install requests
pip install python-dotenv
pip install opencv-python  # 시스템 opencv 사용 시 생략 가능

# 6. YOLO 모델 다운로드
python download_model.py

# 7. .env 파일 생성
nano .env
# 아래 내용 입력
```

**.env 파일 내용:**
```env
BACKEND_URL=http://YOUR_SERVER_IP:5000
DEVICE_ID=pi-01
YOLO_MODEL_PATH=models/yolo11n.pt
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_FPS=30
CONFIDENCE_THRESHOLD=0.5
ASPECT_RATIO_THRESHOLD=1.5
```

```bash
# 8. 클라이언트 실행
python pi_client.py
```

---

## 프론트엔드 환경 설정

### Node.js 설치 확인

```bash
# Node.js 버전 확인
node --version  # v18 이상 권장
npm --version   # v9 이상 권장
```

### 프론트엔드 설정

```bash
# 1. Front 디렉토리로 이동
cd E:\safefallFullstack-main\Front

# 2. 의존성 설치
npm install

# 3. 개발 서버 실행
npm run dev

# 4. 빌드 (프로덕션)
npm run build
```

---

## 가상환경 확인 방법

### 백엔드 가상환경 확인

```powershell
# Windows
(venv) E:\safefallFullstack-main\Back>

# 프롬프트 앞에 (venv)가 표시되면 활성화됨
```

```bash
# Linux/Mac
(venv) user@host:~/safefallFullstack-main/Back$

# 프롬프트 앞에 (venv)가 표시되면 활성화됨
```

### 설치된 패키지 확인

```bash
# 가상환경 활성화 후
pip list

# 또는
pip freeze
```

---

## 가상환경 비활성화

```bash
# 모든 환경에서 동일
deactivate
```

---

## 문제 해결

### 1. "python: command not found" (Linux/Mac)

```bash
# python3 사용
python3 -m venv venv
```

### 2. "venv\Scripts\activate: cannot be loaded" (Windows PowerShell)

```powershell
# 실행 정책 변경
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 다시 활성화
venv\Scripts\activate
```

### 3. pip 설치 실패

```bash
# pip 캐시 삭제 후 재시도
pip cache purge
pip install -r requirements.txt
```

### 4. OpenCV 설치 오류 (라즈베리파이)

```bash
# 시스템 패키지 사용
sudo apt install -y python3-opencv python3-numpy

# 또는 미리 빌드된 버전 설치
pip install opencv-python-headless
```

### 5. 가상환경이 활성화되지 않음

```bash
# 가상환경 재생성
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

python -m venv venv
```

---

## 전체 설정 체크리스트

### ✅ 백엔드 (Back/)
- [ ] 가상환경 생성 및 활성화
- [ ] requirements.txt 설치
- [ ] init_default_user.py 실행
- [ ] videos/ 디렉토리 생성 확인
- [ ] instance/ 디렉토리 생성 확인
- [ ] python app.py 실행 성공

### ✅ 프론트엔드 (Front/)
- [ ] Node.js 설치 확인
- [ ] npm install 성공
- [ ] npm run dev 실행 성공
- [ ] http://localhost:5173 접속 확인

### ✅ 라즈베리파이 (RASP/)
- [ ] 가상환경 설정 (선택)
- [ ] ultralytics 설치
- [ ] YOLO 모델 다운로드
- [ ] .env 파일 생성
- [ ] BACKEND_URL 설정
- [ ] python pi_client.py 실행 성공

---

## 빠른 설정 스크립트

### Windows 백엔드 설정 (setup_backend.bat)

```batch
@echo off
echo SafeFall Backend Setup
echo =====================

cd Back
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python init_default_user.py

echo.
echo Setup Complete!
echo Run: python app.py
pause
```

### Linux/Mac 백엔드 설정 (setup_backend.sh)

```bash
#!/bin/bash
echo "SafeFall Backend Setup"
echo "====================="

cd Back
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python init_default_user.py

echo ""
echo "Setup Complete!"
echo "Run: python app.py"
```

### 프론트엔드 설정 (setup_frontend.bat / .sh)

```bash
#!/bin/bash
echo "SafeFall Frontend Setup"
echo "======================="

cd Front
npm install

echo ""
echo "Setup Complete!"
echo "Run: npm run dev"
```

---

## 환경별 추천 설정

### 개발 환경
```
백엔드: 가상환경 필수
프론트엔드: 로컬 Node.js
라즈베리파이: 시스템 Python (가상환경 선택)
```

### 프로덕션 환경
```
백엔드: Docker 컨테이너 권장
프론트엔드: 빌드 후 Nginx 서빙
라즈베리파이: 시스템 Python + systemd 서비스
```

---

## 추가 도구 (선택사항)

### pyenv (Python 버전 관리)
```bash
# Python 3.11 설치 예시
pyenv install 3.11.0
pyenv local 3.11.0
```

### conda (Anaconda 환경)
```bash
# conda 가상환경 생성
conda create -n safefall python=3.11
conda activate safefall
pip install -r requirements.txt
```

---

## 실행 순서 요약

```
1. 백엔드 가상환경 활성화
   cd Back
   venv\Scripts\activate  (Windows)
   source venv/bin/activate  (Linux/Mac)

2. 백엔드 실행
   python app.py

3. 프론트엔드 실행 (새 터미널)
   cd Front
   npm run dev

4. 라즈베리파이 실행 (라즈베리파이에서)
   cd RASP
   python pi_client.py

5. 테스트 (선택, 새 터미널)
   cd safefallFullstack-main
   python test_integration.py
```

---

**이제 설정을 시작하세요!** 🚀
