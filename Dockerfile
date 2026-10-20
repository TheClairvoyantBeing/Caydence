# =============================================================================
# Caydence — Cinematic Audio Drama & Industrial Narration Engine
# Multi-platform Container Image for GitHub Packages (GHCR)
# =============================================================================
FROM python:3.11-slim

# Prevent bytecode creation and force unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build compiler and system audio/DSP codecs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specifications first for Docker cache optimization
COPY pyproject.toml requirements.txt /app/

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy codebase
COPY . /app/

# Install caydence package in production mode
RUN pip install --no-cache-dir .

# Default entrypoint runs the caydence CLI
ENTRYPOINT ["caydence"]
CMD ["--help"]
