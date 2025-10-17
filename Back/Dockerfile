FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치 (OpenCV 의존성)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 애플리케이션 파일 복사
COPY . .

# instance 디렉토리 생성
RUN mkdir -p instance videos

# 환경 변수 설정
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Gunicorn으로 실행
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
