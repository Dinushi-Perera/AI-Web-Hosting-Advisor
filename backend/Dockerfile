FROM grafana/k6:2.2.0 AS k6-runtime
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=k6-runtime /usr/bin/k6 /usr/local/bin/k6
RUN useradd -m -u 10001 appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p storage/reports storage/load_tests storage/avatars storage/datasets && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
