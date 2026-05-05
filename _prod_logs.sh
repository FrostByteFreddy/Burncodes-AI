#!/bin/bash
# _prod_logs.sh
# Stream production logs from all services or a specific one.
#
# Usage:
#   ./_prod_logs.sh              → all containers (backend + workers + redis)
#   ./_prod_logs.sh backend      → Flask API only
#   ./_prod_logs.sh worker       → both Celery workers (heavy + chat)
#   ./_prod_logs.sh heavy        → celery_worker_heavy only
#   ./_prod_logs.sh chat         → celery_worker_chat only
#   ./_prod_logs.sh file         → tail the file-based app.log (old behaviour)
#   ./_prod_logs.sh errors       → tail error.log file

SERVER="root@142.132.206.182"
APP_DIR="/var/www/burncodes-ai"
COMPOSE="docker compose -f $APP_DIR/docker-compose.prod.yml"
LOG_DIR="/var/lib/docker/volumes/burncodes-ai_app_data/_data/logs"

case "${1:-all}" in
  backend|api|b)
    LABEL="backend (Flask API)"
    CMD="$COMPOSE logs -f --tail=80 backend"
    ;;
  heavy|h)
    LABEL="celery_worker_heavy"
    CMD="$COMPOSE logs -f --tail=80 celery_worker_heavy"
    ;;
  chat|c)
    LABEL="celery_worker_chat"
    CMD="$COMPOSE logs -f --tail=80 celery_worker_chat"
    ;;
  worker|workers|w)
    LABEL="all Celery workers"
    CMD="$COMPOSE logs -f --tail=80 celery_worker_heavy celery_worker_chat"
    ;;
  file|app)
    LABEL="file → app.log"
    CMD="tail -n 80 -f $LOG_DIR/app.log"
    ;;
  errors|error|err|e)
    LABEL="file → error.log"
    CMD="tail -n 80 -f $LOG_DIR/error.log"
    ;;
  debug|d)
    LABEL="file → debug.log"
    CMD="tail -n 80 -f $LOG_DIR/debug.log"
    ;;
  all|*)
    LABEL="ALL containers"
    CMD="$COMPOSE logs -f --tail=50 backend celery_worker_heavy celery_worker_chat celery_beat"
    ;;
esac

echo "📡 Streaming $LABEL from $SERVER"
echo "   (Ctrl+C to stop)"
echo "──────────────────────────────────────────────────────────────"

ssh -t "$SERVER" "$CMD"
