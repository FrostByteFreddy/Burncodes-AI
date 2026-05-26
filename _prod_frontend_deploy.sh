#!/bin/bash
# _prod_frontend_deploy.sh
# Deploys only the frontend service — skips all backend/worker builds so
# Playwright binaries are never re-installed unnecessarily.
#
# Use this for purely frontend changes (Vue, CSS, i18n, etc.).
# Use _prod_deploy.sh when backend or worker code changes.

set -e

SERVER="root@142.132.206.182"
APP_DIR="/var/www/burncodes-ai"
DOMAIN="ai.burn.codes"

echo "=========================================================="
echo "🎨 Frontend-only deploy to $DOMAIN ($SERVER)"
echo "=========================================================="

# 1. Sync only the frontend directory (plus docker-compose in case it changed)
echo "📦 Syncing frontend code to server..."
rsync -avz \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'frontend/dist' \
  frontend/       "$SERVER:$APP_DIR/frontend/"
# Also sync compose files in case a frontend service definition changed
rsync -avz \
  docker-compose.prod.yml \
  nginx/ \
  "$SERVER:$APP_DIR/"

echo "✅ Files synced."

# 2. Rebuild and restart ONLY the frontend container
echo "🔧 Rebuilding frontend container (no-cache)..."
ssh "$SERVER" <<EOF
  set -e
  cd $APP_DIR

  # Rebuild just the frontend image — never uses cache so Vue changes
  # are always picked up. Does NOT touch backend, workers, or nginx.
  docker compose -f docker-compose.prod.yml build --no-cache frontend

  # Hot-swap the frontend container with zero other-service disruption
  docker compose -f docker-compose.prod.yml up -d --no-deps frontend

  echo "✅ Frontend container replaced."
EOF

echo "=========================================================="
echo "🎉 FRONTEND DEPLOY COMPLETE"
echo "   https://$DOMAIN"
echo "=========================================================="
