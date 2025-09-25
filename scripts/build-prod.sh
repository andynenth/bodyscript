#!/bin/bash
# Build production Docker image for BodyScript
# Based on proven workflow pattern with version management and health checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🏗️  Building BodyScript for production..."
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command_exists docker; then
    echo -e "${RED}❌ Docker not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites met${NC}"
echo ""

# Read current version
if [ -f VERSION ]; then
    CURRENT_VERSION=$(cat VERSION)
else
    CURRENT_VERSION="0.0.0"
    echo "$CURRENT_VERSION" > VERSION
fi

# Parse version components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Increment patch version (you can change this logic)
PATCH=$((PATCH + 1))
NEW_VERSION="$MAJOR.$MINOR.$PATCH"

echo "📦 Version Management:"
echo "   Current version: $CURRENT_VERSION"
echo "   New version:     $NEW_VERSION"
echo ""

# Update VERSION file
echo "$NEW_VERSION" > VERSION

# Set image names
IMAGE_NAME="bodyscript"
IMAGE_TAG="$NEW_VERSION"
IMAGE_FULL="$IMAGE_NAME:$IMAGE_TAG"
IMAGE_LATEST="$IMAGE_NAME:latest"

echo "🐳 Building Docker image: $IMAGE_FULL"
echo ""

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose down 2>/dev/null || true
echo ""

# Build the Docker image
echo "🔨 Building Docker image..."
docker build \
    --no-cache \
    --build-arg VERSION=$NEW_VERSION \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --tag $IMAGE_FULL \
    --tag $IMAGE_LATEST \
    .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker image built successfully${NC}"
echo ""

# Test the Docker image locally
echo "🧪 Testing Docker image locally..."

# Start container with production config
docker-compose -f docker-compose.prod.yml up -d

# Wait for container to be healthy
echo "⏳ Waiting for container to be healthy..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Container is healthy${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}❌ Container failed health check${NC}"
        docker-compose -f docker-compose.prod.yml logs --tail=20
        docker-compose -f docker-compose.prod.yml down
        exit 1
    fi

    sleep 1
    echo -n "."
done
echo ""

# Run basic smoke tests
echo "🔬 Running smoke tests..."

# Test API health endpoint
echo -n "  Testing /health endpoint: "
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    docker-compose -f docker-compose.prod.yml down
    exit 1
fi

# Test API documentation
echo -n "  Testing /docs endpoint: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${YELLOW}⚠️ (HTTP $HTTP_CODE)${NC}"
    # Non-critical, don't exit
fi

# Check memory usage
echo ""
echo "📊 Container resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo ""

# Stop test container
echo "🛑 Stopping test container..."
docker-compose -f docker-compose.prod.yml down
echo ""

# Save image for transfer
echo "💾 Saving Docker image for transfer..."
IMAGE_FILE="bodyscript-${NEW_VERSION}.tar"
docker save -o $IMAGE_FILE $IMAGE_FULL $IMAGE_LATEST

if [ -f "$IMAGE_FILE" ]; then
    SIZE=$(ls -lh $IMAGE_FILE | awk '{print $5}')
    echo -e "${GREEN}✅ Image saved: $IMAGE_FILE (${SIZE})${NC}"
else
    echo -e "${RED}❌ Failed to save image${NC}"
    exit 1
fi

echo ""
echo "📦 Build Summary:"
echo "────────────────"
echo "Version:     $NEW_VERSION"
echo "Image:       $IMAGE_FULL"
echo "File:        $IMAGE_FILE"
echo "Next step:   Run ./scripts/deploy-ec2.sh to deploy"
echo ""
echo -e "${GREEN}✨ Build completed successfully!${NC}"