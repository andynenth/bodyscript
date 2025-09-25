#!/bin/bash
# Deploy BodyScript to EC2 with Option C architecture (Nginx + Docker API)
# Based on proven workflow with image transfer and SSL setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Hardcoded configuration for BodyScript EC2
EC2_HOST="98.81.229.113"
EC2_USER="ubuntu"
SSH_KEY="/Users/nrw/.ssh/bodyscript-key.pem"
DOMAIN="bodyscript.andynenth.dev"
PROJECT_DIR="/home/ubuntu/bodyscript"

echo "🚀 Deploying BodyScript to EC2"
echo "════════════════════════════════"
echo "Host:    $EC2_HOST"
echo "User:    $EC2_USER"
echo "Domain:  $DOMAIN"
echo "SSH Key: $SSH_KEY"
echo ""

# Check if build exists
if [ ! -f VERSION ]; then
    echo -e "${RED}❌ VERSION file not found. Run build-prod.sh first${NC}"
    exit 1
fi

VERSION=$(cat VERSION)
IMAGE_FILE="bodyscript-${VERSION}.tar"

if [ ! -f "$IMAGE_FILE" ]; then
    echo -e "${RED}❌ Image file not found: $IMAGE_FILE${NC}"
    echo "   Run ./scripts/build-prod.sh first"
    exit 1
fi

echo "📦 Deploying version: $VERSION"
echo ""

# SSH command helper
ssh_cmd() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "$@"
}

# SCP command helper
scp_cmd() {
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$@"
}

# Step 1: Check SSH connection
echo "🔑 Testing SSH connection..."
if ssh_cmd "echo 'Connected successfully'" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to EC2 instance${NC}"
    echo "   Check your SSH key and EC2 security group"
    exit 1
fi
echo ""

# Step 2: Prepare EC2 instance
echo "📝 Preparing EC2 instance..."
ssh_cmd "bash -s" << 'EOF'
    set -e

    # Install Docker if not present
    if ! command -v docker >/dev/null 2>&1; then
        echo "Installing Docker..."
        sudo apt-get update
        sudo apt-get install -y docker.io docker-compose
        sudo usermod -aG docker $USER
        sudo systemctl start docker
        sudo systemctl enable docker
    fi

    # Install Nginx if not present
    if ! command -v nginx >/dev/null 2>&1; then
        echo "Installing Nginx..."
        sudo apt-get install -y nginx certbot python3-certbot-nginx
        sudo systemctl start nginx
        sudo systemctl enable nginx
    fi

    # Create project directory
    mkdir -p ~/bodyscript/{nginx,scripts,backend/temp}

    echo "✅ EC2 instance prepared"
EOF
echo ""

# Step 3: Transfer Docker image
echo "📤 Transferring Docker image to EC2..."
echo "   File: $IMAGE_FILE ($(ls -lh $IMAGE_FILE | awk '{print $5}'))"

# Use compression for faster transfer
if command -v pv >/dev/null 2>&1; then
    # If pv is available, show progress
    pv "$IMAGE_FILE" | gzip | ssh_cmd "gunzip | docker load"
else
    # Otherwise, simple transfer
    gzip < "$IMAGE_FILE" | ssh_cmd "gunzip | docker load"
fi

echo -e "${GREEN}✅ Docker image transferred${NC}"
echo ""

# Step 4: Transfer configuration files
echo "📋 Transferring configuration files..."

# Create temporary directory for configs
TEMP_CONFIG=$(mktemp -d)
trap "rm -rf $TEMP_CONFIG" EXIT

# Copy necessary files
cp docker-compose.prod.yml "$TEMP_CONFIG/"
cp -r nginx "$TEMP_CONFIG/"
cp -r scripts "$TEMP_CONFIG/"

# Create .env.prod file
cat > "$TEMP_CONFIG/.env.prod" << 'ENVEOF'
ENVIRONMENT=production
API_BASE_URL=https://bodyscript.andynenth.dev
FRONTEND_URL=https://bodyscript.andynenth.dev
PROCESSING_MAX_SIZE_MB=50
PROCESSING_TIMEOUT_SECONDS=300
SERVE_STATIC=false
ENVEOF

# Transfer files INCLUDING .env.prod (hidden file)
scp_cmd -r "$TEMP_CONFIG/." "$EC2_USER@$EC2_HOST:$PROJECT_DIR/"

echo -e "${GREEN}✅ Configuration files transferred${NC}"
echo ""

# Step 5: Configure Nginx on EC2
echo "🌐 Configuring Nginx..."
ssh_cmd "bash -s" << EOF
    set -e

    # Create Nginx configuration for Option C
    sudo tee /etc/nginx/sites-available/bodyscript > /dev/null << NGINX_CONFIG
server {
    listen 80;
    server_name $DOMAIN;

    # Redirect HTTP to HTTPS (will be enabled after SSL setup)
    # return 301 https://\$server_name\$request_uri;

    # Frontend static files served directly by Nginx
    location / {
        root $PROJECT_DIR/frontend;
        try_files \$uri \$uri.html \$uri/ /index.html;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
    }

    # API routes proxied to Docker container
    location /api {
        proxy_pass http://localhost:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for long processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;

        # File upload size limit
        client_max_body_size 50M;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
    }

    # Static assets with aggressive caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root $PROJECT_DIR/frontend;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Disable access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
NGINX_CONFIG

    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/bodyscript /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default

    # Test Nginx configuration
    sudo nginx -t

    echo "✅ Nginx configured"
EOF
echo ""

# Step 6: Transfer frontend files
echo "📁 Transferring frontend files..."

# Create tar of frontend files (excluding node_modules if present)
tar czf frontend.tar.gz --exclude='node_modules' --exclude='.git' frontend/

# Transfer and extract
scp_cmd frontend.tar.gz "$EC2_USER@$EC2_HOST:$PROJECT_DIR/"
ssh_cmd "cd $PROJECT_DIR && tar xzf frontend.tar.gz && rm frontend.tar.gz"

# Fix permissions for Nginx to access files
ssh_cmd "chmod 755 /home/ubuntu && chmod -R 755 $PROJECT_DIR/frontend"

rm frontend.tar.gz

echo -e "${GREEN}✅ Frontend files transferred${NC}"
echo ""

# Step 7: Start Docker container
echo "🐳 Starting Docker container..."
ssh_cmd "bash -s" << EOF
    set -e
    cd $PROJECT_DIR

    # Stop any existing containers
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

    # Start container with production config
    docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

    # Wait for container to be healthy
    echo "Waiting for container to be healthy..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            echo "✅ Container is healthy"
            break
        fi
        if [ \$i -eq 30 ]; then
            echo "❌ Container failed health check"
            docker-compose -f docker-compose.prod.yml logs --tail=20
            exit 1
        fi
        sleep 1
        echo -n "."
    done
EOF
echo ""

# Step 8: Restart Nginx
echo "♻️  Restarting Nginx..."
ssh_cmd "sudo systemctl reload nginx"
echo -e "${GREEN}✅ Nginx restarted${NC}"
echo ""

# Step 9: Setup SSL with Let's Encrypt
echo "🔒 Setting up SSL certificate..."
read -p "Do you want to setup SSL with Let's Encrypt? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ssh_cmd "sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN --redirect"
    echo -e "${GREEN}✅ SSL configured${NC}"
else
    echo -e "${YELLOW}⚠️  SSL setup skipped${NC}"
fi
echo ""

# Step 10: Health check
echo "🏥 Running health checks..."

# Check HTTP/HTTPS
if curl -f "http://$EC2_HOST/health" >/dev/null 2>&1; then
    echo -e "  HTTP Health:  ${GREEN}✅${NC}"
else
    echo -e "  HTTP Health:  ${RED}❌${NC}"
fi

# Check API docs
if curl -f "http://$EC2_HOST/api/docs" >/dev/null 2>&1; then
    echo -e "  API Docs:     ${GREEN}✅${NC}"
else
    echo -e "  API Docs:     ${RED}❌${NC}"
fi

# Check container status
echo ""
echo "📊 Container status:"
ssh_cmd "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
echo ""

# Step 11: Setup auto-restart
echo "🔄 Setting up auto-restart..."
ssh_cmd "bash -s" << 'EOF'
    # Create systemd service for Docker Compose
    sudo tee /etc/systemd/system/bodyscript.service > /dev/null << 'SERVICE'
[Unit]
Description=BodyScript Docker Application
Requires=docker.service
After=docker.service

[Service]
Type=simple
WorkingDirectory=/home/ubuntu/bodyscript
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml --env-file .env.prod up
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
SERVICE

    sudo systemctl daemon-reload
    sudo systemctl enable bodyscript
    echo "✅ Auto-restart configured"
EOF
echo ""

# Step 12: Cleanup
echo "🧹 Cleaning up..."
ssh_cmd "bash -s" << EOF
    # Remove old Docker images
    docker image prune -f

    # Clean apt cache
    sudo apt-get clean

    echo "✅ Cleanup complete"
EOF
echo ""

# Display summary
echo "════════════════════════════════════════"
echo "🎉 Deployment Complete!"
echo "════════════════════════════════════════"
echo ""
echo "📌 Access Points:"
echo "   Web:    http://$DOMAIN"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Secure: https://$DOMAIN"
fi
echo "   API:    http://$DOMAIN/api/docs"
echo ""
echo "📊 Version Deployed: $VERSION"
echo ""
echo "🔧 Useful Commands:"
echo "   SSH:         ssh -i $SSH_KEY $EC2_USER@$EC2_HOST"
echo "   Logs:        ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml logs -f'"
echo "   Restart:     ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'sudo systemctl restart bodyscript'"
echo "   Status:      ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'docker ps'"
echo ""
echo -e "${GREEN}✨ Deployment successful!${NC}"