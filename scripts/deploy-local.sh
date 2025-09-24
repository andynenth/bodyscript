#!/bin/bash
set -e

echo "🚀 Starting local development environment..."

# Use local environment
export ENV_FILE=.env.local

# Check if .env.local exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: $ENV_FILE not found!"
    echo "Please create it from .env.example or .env.local template"
    exit 1
fi

# Build and start
echo "📦 Building Docker image..."
docker-compose --env-file $ENV_FILE build

echo "🏃 Starting containers..."
docker-compose --env-file $ENV_FILE up

echo "✅ Local environment running at http://localhost:8000"