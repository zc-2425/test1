FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /srv/app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
RUN mv app/main.py app/main.rollback-drill

USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
