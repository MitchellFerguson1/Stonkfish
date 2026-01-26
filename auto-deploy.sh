#!/bin/bash

# Auto-deploy script for Stonkfish
# Checks for new commits on main and rebuilds if needed

# Use system Docker socket
export DOCKER_HOST=unix:///var/run/docker.sock

cd ~/Stonkfish || exit 1

# Fetch latest from remote
git fetch origin main --quiet

# Get current and remote commit hashes
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "$(date): New changes detected, deploying..."

    git reset --hard origin/main

    # Ensure data directory exists
    mkdir -p data

    # Rebuild and restart
    docker compose down
    docker compose up -d --build

    echo "$(date): Deploy complete"
else
    echo "$(date): No changes"
fi
