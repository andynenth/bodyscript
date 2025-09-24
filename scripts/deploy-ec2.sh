#!/bin/bash
set -e

echo "🚀 Deploying to EC2..."

# Load production environment
export ENV_FILE=.env.production

# Check if .env.production exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: $ENV_FILE not found!"
    echo "Please create it from .env.production template"
    exit 1
fi

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Build with cache
echo "📦 Building Docker image..."
docker-compose --env-file $ENV_FILE build

# Stop old container
echo "🛑 Stopping old containers..."
docker-compose --env-file $ENV_FILE down

# Start new container
echo "🏃 Starting new containers..."
docker-compose --env-file $ENV_FILE up -d

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Check health
echo "🏥 Checking health..."
if curl -f http://localhost:8000/health; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    echo "Checking logs..."
    docker-compose --env-file $ENV_FILE logs --tail=50
    exit 1
fi

echo "✅ Deployment complete!"
echo "📊 Memory usage:"
docker stats --no-stream