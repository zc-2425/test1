# 后端镜像：FastAPI + uvicorn（SQLite 随容器数据卷持久化）
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

# 先装依赖，改代码时可复用这层缓存
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

# data（sqlite）与 uploads 由 compose 挂数据卷，容器内保留目录即可
RUN mkdir -p /app/data /app/uploads

EXPOSE 5274
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5274"]
