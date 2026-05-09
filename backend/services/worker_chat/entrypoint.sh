#!/bin/sh
# Create required data directories with correct permissions before starting the app
mkdir -p /app/data/logs /app/data/chromadb /app/data/uploads
chown -R appuser:appgroup /app/data
exec gosu appuser "$@"
