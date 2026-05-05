#!/bin/bash
# logs.sh
# Stream tail the live backend log from the production server.
# Usage:
#   ./logs.sh            → tail app.log (INFO+ — default)
#   ./logs.sh errors     → tail error.log (ERROR+ only)
#   ./logs.sh debug      → tail debug.log (everything, verbose)

SERVER="root@142.132.206.182"
LOG_DIR="/var/lib/docker/volumes/burncodes-ai_app_data/_data/logs"

case "${1:-app}" in
  errors|error|err|e)
    LOG_FILE="$LOG_DIR/error.log"
    LABEL="ERROR log"
    ;;
  debug|d|verbose|v)
    LOG_FILE="$LOG_DIR/debug.log"
    LABEL="DEBUG log (verbose)"
    ;;
  *)
    LOG_FILE="$LOG_DIR/app.log"
    LABEL="APP log"
    ;;
esac

echo "📡 Streaming $LABEL from $SERVER"
echo "   File: $LOG_FILE"
echo "   (Ctrl+C to stop)"
echo "──────────────────────────────────────────────────────────────"

ssh -t "$SERVER" "tail -n 50 -f $LOG_FILE"
