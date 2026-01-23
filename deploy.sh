#!/bin/bash

# Stonkfish Deployment Script
# Usage: ./deploy.sh username@your-server.com

if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh username@server.com"
    exit 1
fi

SERVER=$1
REMOTE_PATH="/home/$(echo $SERVER | cut -d'@' -f1)/Stonkfish"

echo "🚀 Deploying Stonkfish to $SERVER..."

# Sync files to server
rsync -avz --progress \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude 'portfolio_data.json' \
    --exclude 'venv' \
    --exclude '.env' \
    --exclude 'deploy.sh' \
    ./ $SERVER:$REMOTE_PATH/

echo "✅ Files transferred!"
echo ""
echo "📋 Next steps:"
echo "1. SSH into your server: ssh $SERVER"
echo "2. cd $REMOTE_PATH"
echo "3. Create .env file: cp .env.template .env && nano .env"
echo "4. Start the bot: docker-compose up -d"
echo "5. View logs: docker-compose logs -f"
