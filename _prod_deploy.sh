#!/bin/bash
# deploy.sh
# Automates the deployment of Burncodes AI to the production server.

set -e

# Production server details
SERVER="root@142.132.206.182"
APP_DIR="/var/www/burncodes-ai"
DOMAIN="ai.burn.codes"

echo "=========================================================="
echo "🚀 Deploying Burncodes AI to $DOMAIN ($SERVER)"
echo "=========================================================="

# 1. Sync files to the server
echo "📦 Syncing code directly to server inside $APP_DIR..."
# Ensure directory exists on the remote
ssh "$SERVER" "mkdir -p $APP_DIR"
# Sync over
rsync -avz \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'backend/venv' \
  --exclude 'backend/__pycache__' \
  --exclude 'frontend/dist' \
  --exclude '.env.*' \
  ./ "$SERVER:$APP_DIR"

echo "✅ Code synced successfully."

# 2. Setup server via SSH
echo "🔧 Configuring production server..."
ssh "$SERVER" << EOF
  set -e
  
  # Install Docker if not present
  if ! command -v docker &> /dev/null; then
      echo "🐳 Docker not found. Installing Docker..."
      curl -fsSL https://get.docker.com | sh
  fi

  cd $APP_DIR

  # Setup Let's Encrypt certificates if they don't exist
  if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
      echo "🔐 SSL Certificates not found for $DOMAIN. Provisioning now..."
      
      # Ensure certbot is installed
      if ! command -v certbot &> /dev/null; then
          apt-get update
          apt-get install -y certbot
      fi
      
      # Stop anything holding port 80 just in case
      docker compose -f docker-compose.prod.yml down || true
      
      # Run standalone certbot
      certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos -m moritz.burn@gmail.com
      echo "✅ SSL Certificates successfully provisioned."
  else
      echo "✅ SSL Certificates already exist for $DOMAIN."
  fi

  # Build backend with layer cache (pip + playwright only reinstall when requirements.txt changes)
  docker compose -f docker-compose.prod.yml build backend celery_worker_fast celery_worker_heavy celery_beat

  # Always force-rebuild the frontend so Vue code changes are never skipped
  # (no Playwright here, so this is fast: just npm ci + vite build)
  docker compose -f docker-compose.prod.yml build --no-cache frontend

  docker compose -f docker-compose.prod.yml up -d --force-recreate

  echo "🔓 Fixing data directory permissions..."
  docker compose -f docker-compose.prod.yml exec -T backend \
    sh -c 'chmod -R 777 /app/data && echo "✅ Permissions fixed on /app/data"'

  echo "✅ Containers are running!"
EOF

echo "=========================================================="
echo "🎉 DEPLOYMENT COMPLETE"
echo "Check https://$DOMAIN to see if everything is up."
echo "=========================================================="
