FROM python:3.12-bookworm

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install git and other utilities
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace
