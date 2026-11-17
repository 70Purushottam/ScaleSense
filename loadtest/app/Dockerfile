FROM python:3.12-slim
WORKDIR /srv
RUN pip install --no-cache-dir fastapi uvicorn asyncpg redis
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]