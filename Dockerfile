# syntax=docker/dockerfile:1
FROM python:3.8-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY src/camelgo/cert.pem src/camelgo/key.pem ./src/camelgo/

RUN pip install uv_build && pip install . && pip install flask dash dash-bootstrap-components

EXPOSE 8080
ENTRYPOINT ["python", "src/camelgo/dash_app.py"]
