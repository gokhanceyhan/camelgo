# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY local/ ./src/camelgo/application

RUN pip install uv_build && pip install .

EXPOSE 8080
ENTRYPOINT ["python", "src/camelgo/application/dash_app.py"]
