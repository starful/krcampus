FROM python:3.11-slim

WORKDIR /code

# 1. 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. 필수 앱 소스 복사
# app 폴더 전체 복사
COPY app ./app
# [수정] scripts 폴더 전체 복사 (build_data.py가 여기 포함됨)
COPY scripts ./scripts

# 3. 빌드 시점에 Markdown -> JSON 변환 실행
# [수정] 경로 변경 반영
RUN python scripts/build_data.py

# 4. 실행 설정
ENV PORT=8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]