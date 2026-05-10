FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 APP_HOME=/app
WORKDIR $APP_HOME

RUN apt-get update && apt-get install -y --no-install-recommends gosu && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --home /home/appuser appuser && \
    mkdir -p /home/appuser && chown -R appuser:appgroup /home/appuser

COPY services/worker_heavy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright browsers (only this image)
ENV GRPC_ENABLE_FORK_SUPPORT=False
ENV PLAYWRIGHT_BROWSERS_PATH=0
RUN playwright install-deps && playwright install

ENV XDG_CONFIG_HOME=/tmp/.chromium XDG_CACHE_HOME=/tmp/.chromium
ENV HOME=/home/appuser
ENV CRAWL4AI_HOME=/home/appuser/.crawl4ai
RUN mkdir -p /home/appuser/.local /home/appuser/.config /home/appuser/.cache /home/appuser/.pki /home/appuser/.crawl4ai && \
    chown -R appuser:appgroup /home/appuser/.local /home/appuser/.config /home/appuser/.cache /home/appuser/.pki /home/appuser/.crawl4ai

COPY services/worker_heavy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY services/worker_heavy/app/ app/
COPY shared/auth/         app/auth/
COPY shared/database/     app/database/
COPY shared/models/       app/models/
COPY shared/logging_config.py app/logging_config.py
COPY shared/gemini_store/    app/gemini_store/

COPY services/worker_heavy/celery_worker.py .
RUN chown -R appuser:appgroup $APP_HOME

ENTRYPOINT ["/entrypoint.sh"]
CMD ["celery", "-A", "celery_worker.celery", "worker", "--loglevel=info", "--queues=heavy", "--concurrency=1", "--hostname=heavy@%h"]
