# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

# Create a non-root user and group
# --system creates a user without a password or home directory
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# 1. Install Python dependencies
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Install Playwright browsers and dependencies (as root)
ENV PLAYWRIGHT_BROWSERS_PATH=0
RUN playwright install-deps
RUN playwright install

# 3. Copy your application code into the container
COPY . .

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appgroup $APP_HOME

# Switch to the non-root user
USER appuser