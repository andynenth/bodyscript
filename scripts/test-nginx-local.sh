#!/bin/bash
# Test script for Option C: Nginx serving static + Docker API
# Run this on your local Mac to test the architecture before EC2 deployment

set -e

echo "🧪 Testing Nginx + Docker architecture locally..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."

    # Stop Docker container
    docker-compose -f docker-compose.nginx.yml down 2>/dev/null || true

    # Stop Nginx
    if command_exists nginx; then
        nginx -s stop 2>/dev/null || true
    fi

    echo "✅ Cleanup complete"
}

# Set trap for cleanup
trap cleanup EXIT

# Step 1: Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists nginx; then
    echo -e "${RED}❌ Nginx not installed${NC}"
    echo "   Install with: brew install nginx"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${RED}❌ Docker not installed${NC}"
    echo "   Install Docker Desktop for Mac"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"
echo ""

# Step 2: Stop any existing services
echo "🛑 Stopping existing services..."

# Stop any running uvicorn
pkill -f "uvicorn" 2>/dev/null || true

# Stop existing Docker containers
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.nginx.yml down 2>/dev/null || true

# Stop Nginx if running
nginx -s stop 2>/dev/null || true

echo "✅ Existing services stopped"
echo ""

# Step 3: Start Docker container (API only)
echo "🐋 Starting Docker container (API only)..."

# Set environment for API-only mode
export SERVE_STATIC=false
export ENVIRONMENT=development

# Build and start container
docker-compose -f docker-compose.nginx.yml --env-file .env.local build
docker-compose -f docker-compose.nginx.yml --env-file .env.local up -d

# Wait for container to be healthy
echo "⏳ Waiting for API to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ API is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ API failed to start${NC}"
        docker-compose -f docker-compose.nginx.yml logs --tail=20
        exit 1
    fi
    sleep 1
    echo -n "."
done
echo ""

# Step 4: Configure and start Nginx
echo "🌐 Starting Nginx..."

# Create symlink to our config (Nginx on Mac looks in /usr/local/etc/nginx/servers/)
NGINX_CONF_DIR="/usr/local/etc/nginx/servers"
mkdir -p "$NGINX_CONF_DIR"

# Remove any existing symlink
rm -f "$NGINX_CONF_DIR/bodyscript.conf"

# Create new symlink
ln -s "$(pwd)/nginx/local.conf" "$NGINX_CONF_DIR/bodyscript.conf"

# Test Nginx configuration
if nginx -t 2>/dev/null; then
    echo -e "${GREEN}✅ Nginx configuration valid${NC}"
else
    echo -e "${RED}❌ Nginx configuration error${NC}"
    nginx -t
    exit 1
fi

# Start Nginx
nginx

echo -e "${GREEN}✅ Nginx started${NC}"
echo ""

# Step 5: Test endpoints
echo "🧪 Testing endpoints..."
echo ""

# Test static file serving (Nginx)
echo -n "Testing homepage (Nginx static): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

# Test clean URLs (Nginx)
echo -n "Testing /upload clean URL (Nginx): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost/upload | grep -q "200"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

# Test API proxy (Nginx → Docker)
echo -n "Testing API health (via proxy): "
if curl -s http://localhost/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

# Test direct API access (Docker)
echo -n "Testing API direct access: "
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

# Test static assets
echo -n "Testing CSS file (cached): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost/css/main.css | grep -q "200"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

echo ""
echo "📊 Service Status:"
echo "─────────────────"
echo "Nginx:  http://localhost/ (serving frontend)"
echo "API:    http://localhost:8000/api (Docker container)"
echo "Proxy:  http://localhost/api → localhost:8000/api"
echo ""

# Step 6: Show logs
echo "📝 Recent logs:"
echo ""
echo "Docker API logs:"
docker-compose -f docker-compose.nginx.yml logs --tail=5
echo ""

# Step 7: Memory usage
echo "💾 Memory usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}"
echo ""

echo "✨ Test complete!"
echo ""
echo "Access the application at: ${GREEN}http://localhost/${NC}"
echo ""
echo "To stop all services, press Ctrl+C or run:"
echo "  docker-compose -f docker-compose.nginx.yml down"
echo "  nginx -s stop"
echo ""

# Keep running to show logs
echo "Press Ctrl+C to stop..."
docker-compose -f docker-compose.nginx.yml logs -f