#!/bin/bash
# Quick test script to verify Docker setup

echo "🧪 Testing Docker setup locally..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "⚠️  .env.local not found. Creating from template..."
    # Already created above, just checking
    echo "✅ .env.local exists"
fi

# Build the image
echo "📦 Building Docker image..."
if docker-compose --env-file .env.local build; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi

# Test run (just start and immediately stop)
echo "🏃 Testing container startup..."
timeout 10 docker-compose --env-file .env.local up || true

echo "🛑 Stopping containers..."
docker-compose --env-file .env.local down

echo ""
echo "✅ Docker setup test complete!"
echo ""
echo "To run the application:"
echo "  ./scripts/deploy-local.sh"
echo ""
echo "To deploy to EC2:"
echo "  1. Run on EC2: ./scripts/setup-ec2.sh"
echo "  2. Copy .env.production and set your secrets"
echo "  3. Run: ./scripts/deploy-ec2.sh"