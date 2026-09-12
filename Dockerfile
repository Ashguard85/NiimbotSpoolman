FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app /app/app
RUN mkdir -p /app/data/backups
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=4s --start-period=8s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=2).read()" || exit 1
CMD ["gunicorn","--chdir","/app/app","--bind","0.0.0.0:8080","--workers","2","--threads","4","--timeout","30","app:app"]
