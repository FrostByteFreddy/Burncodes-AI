FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 APP_HOME=/app
WORKDIR $APP_HOME

RUN apt-get update && apt-get install -y --no-install-recommends gosu && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    mkdir -p /home/appuser && chown -R appuser:appgroup /home/appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY app/ app/
COPY celery_worker.py .
RUN chown -R appuser:appgroup $APP_HOME

ENTRYPOINT ["/entrypoint.sh"]
CMD ["celery", "-A", "celery_worker.celery", "worker", "--loglevel=info", "--queues=chat", "--concurrency=4", "--hostname=chat@%h"]
