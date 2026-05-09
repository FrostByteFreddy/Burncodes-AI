FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 APP_HOME=/app
WORKDIR $APP_HOME

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    mkdir -p /home/appuser && chown -R appuser:appgroup /home/appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY celery_beat.py .
RUN chown -R appuser:appgroup $APP_HOME

USER appuser
CMD ["celery", "-A", "celery_beat.celery", "beat", "--loglevel=info"]
