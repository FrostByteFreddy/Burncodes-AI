FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 APP_HOME=/app
WORKDIR $APP_HOME

RUN apt-get update && apt-get install -y --no-install-recommends gosu && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    mkdir -p /home/appuser && chown -R appuser:appgroup /home/appuser

# Build context is ./backend — prefix all paths with services/api/
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/api/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy service-specific app/ first, then overwrite with shared modules.
# Shared modules live in backend/shared/ and are symlinked inside app/ for
# local dev — we copy the real files here to avoid symlink resolution issues.
COPY services/api/app/ app/
COPY shared/auth/       app/auth/
COPY shared/database/   app/database/
COPY shared/models/     app/models/
COPY shared/logging_config.py app/logging_config.py

COPY services/api/run.py .
RUN chown -R appuser:appgroup $APP_HOME

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "run.py"]
