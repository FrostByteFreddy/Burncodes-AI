FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 APP_HOME=/app
WORKDIR $APP_HOME

RUN apt-get update && apt-get install -y --no-install-recommends gosu && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    mkdir -p /home/appuser && chown -R appuser:appgroup /home/appuser

COPY services/worker_fast/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/worker_fast/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY services/worker_fast/app/ app/
COPY shared/auth/         app/auth/
COPY shared/database/     app/database/
COPY shared/models/       app/models/
COPY shared/logging_config.py app/logging_config.py

COPY services/worker_fast/celery_worker.py .
RUN chown -R appuser:appgroup $APP_HOME

ENTRYPOINT ["/entrypoint.sh"]
CMD ["celery", "-A", "celery_worker.celery", "worker", "--loglevel=info", "--queues=fast", "--concurrency=8", "--hostname=fast@%h"]
