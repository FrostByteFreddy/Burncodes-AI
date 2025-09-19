# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

# Create a non-root user, group, and a dedicated home directory <--- CHANGE
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --home /home/appuser --create-home appuser

# 1. Install Python dependencies
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Install Playwright browsers and dependencies (as root)
ENV PLAYWRIGHT_BROWSERS_PATH=0
RUN playwright install-deps
RUN playwright install

# 3. Create required directories in the CORRECT home directory <--- CHANGE
RUN CHROME_DIRS="/home/appuser/.local /home/appuser/.config /home/appuser/.cache /home/appuser/.pki" && \
    mkdir -p ${CHROME_DIRS} && \
    chown -R appuser:appgroup ${CHROME_DIRS}

# 4. Copy your application code into the container
COPY . .

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appgroup $APP_HOME

# Switch to the non-root user
USER appuser