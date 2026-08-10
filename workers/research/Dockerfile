FROM python:3.12-slim
WORKDIR /app
COPY services/api/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .
COPY services/api/app ./app
COPY workers/research/worker.py ./worker.py
CMD ["celery","-A","worker.celery","worker","--loglevel=INFO"]
