#!/bin/bash
# deploy.sh
# Automates the deployment of Burncodes AI to the production server.

set -e

# Production server details (overridable, e.g. from the release workflow)
SERVER="${DEPLOY_SERVER:-root@142.132.206.182}"
APP_DIR="${DEPLOY_APP_DIR:-/var/www/burncodes-ai}"
DOMAIN="${DEPLOY_DOMAIN:-ai.burn.codes}"
HEAVY_WORKERS="${DEPLOY_HEAVY_WORKERS:-10}"   # number of worker_heavy containers (each runs 1 Chromium)


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

  # Build with the layer cache. Every Dockerfile installs its dependencies
  # (pip, npm, Playwright's Chromium) before copying the code, so a code change
  # only rebuilds the last layers; dependencies are reinstalled only when
  # requirements.txt / package-lock.json change. Images that come out the same
  # keep their ID, and "up" leaves their containers running.
  docker compose -f docker-compose.prod.yml build

  # Recreate only the containers whose image or settings changed (no "down":
  # redis, nginx and untouched workers keep running, queued tasks stay queued;
  # the watchdog re-sends tasks a restarted worker was holding).
  docker compose -f docker-compose.prod.yml up -d --remove-orphans \
    --scale celery_worker_heavy=$HEAVY_WORKERS

  # nginx resolves backend/frontend to IPs when it starts, and recreated
  # containers get new ones; it also reads nginx.conf only at start. A restart
  # (about a second) picks up both.
  docker compose -f docker-compose.prod.yml restart nginx

  # Old image layers pile up with cached builds; drop the unused ones
  docker image prune -f > /dev/null

  echo "🔓 Fixing data directory permissions..."
  docker compose -f docker-compose.prod.yml exec -T backend \
    sh -c 'chmod -R 777 /app/data && echo "✅ Permissions fixed on /app/data"'

  echo "✅ Containers are running!"
EOF

echo "=========================================================="
echo "🎉 DEPLOYMENT COMPLETE"
echo "Check https://$DOMAIN to see if everything is up."
echo "=========================================================="
