# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

# 1. Install all system and Python dependencies for BOTH services
RUN apt-get update && apt-get install -y \
    libgtk-4-1 \
    libgraphene-1.0-0 \
    # ... and all other system dependencies ...
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Install Playwright browsers
RUN playwright install

# 3. Copy all your application code
COPY . .

# Run commands come from render settings
