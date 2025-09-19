# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

# Create user, group, and home directory using basic commands
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    mkdir -p /home/appuser && \
    chown -R appuser:appgroup /home/appuser

# 1. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Install Playwright browsers and dependencies (as root)
ENV PLAYWRIGHT_BROWSERS_PATH=0
RUN playwright install-deps
RUN playwright install

# Adding this because of chrome_crashpad_handler: --database is required when crawling
ENV XDG_CONFIG_HOME=/tmp/.chromium
ENV XDG_CACHE_HOME=/tmp/.chromium

# 3. Create required directories in the CORRECT home directory
RUN CHROME_DIRS="/home/appuser/.local /home/appuser/.config /home/appuser/.cache /home/appuser/.pki" && \
    mkdir -p ${CHROME_DIRS} && \
    chown -R appuser:appgroup ${CHROME_DIRS}

# 4. Copy your application code into the container
COPY . .

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appgroup $APP_HOME

# Switch to the non-root user
USER appuser