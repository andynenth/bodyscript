#!/bin/bash

# EC2 Native Setup Script for BodyScript
# This script sets up the EC2 instance for native Python deployment (no Docker)

set -e  # Exit on error

# Configuration
EC2_HOST="98.81.229.113"
EC2_USER="ubuntu"
SSH_KEY="$HOME/.ssh/bodyscript-key.pem"
PROJECT_NAME="bodyscript"
REMOTE_DIR="/home/ubuntu/$PROJECT_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}Error: SSH key not found at $SSH_KEY${NC}"
    echo "Please ensure your SSH key is at the correct location"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  EC2 Native Setup for BodyScript${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Target: $EC2_USER@$EC2_HOST${NC}"
echo ""

# Function to run commands on EC2
run_remote() {
    ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "$1"
}

# Step 1: Stop Docker services if running
echo -e "${YELLOW}Step 1: Stopping Docker services (if any)...${NC}"
run_remote "sudo docker stop bodyscript-api 2>/dev/null || true"
run_remote "sudo docker-compose -f $REMOTE_DIR/docker-compose.prod.yml down 2>/dev/null || true"

# Step 2: Backup existing data
echo -e "${YELLOW}Step 2: Backing up existing data...${NC}"
run_remote "if [ -d $REMOTE_DIR/backend/temp ]; then
    echo 'Backing up processed videos...'
    cp -r $REMOTE_DIR/backend/temp $REMOTE_DIR/backend/temp.backup.$(date +%Y%m%d_%H%M%S)
fi"

# Step 3: Install system dependencies
echo -e "${YELLOW}Step 3: Installing system dependencies...${NC}"
# First, add deadsnakes PPA for Python 3.9 if needed
run_remote "sudo add-apt-repository ppa:deadsnakes/ppa -y 2>/dev/null || true"
run_remote "sudo apt-get update && sudo apt-get install -y \
    python3.9 \
    python3.9-venv \
    python3.9-dev \
    python3-pip \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    build-essential"

# Step 4: Create project structure
echo -e "${YELLOW}Step 4: Creating project structure...${NC}"
run_remote "mkdir -p $REMOTE_DIR/{backend,frontend,cli}"

# Step 5: Create Python virtual environment
echo -e "${YELLOW}Step 5: Setting up Python virtual environment...${NC}"
run_remote "cd $REMOTE_DIR && python3.9 -m venv venv"

# Step 6: Copy project files
echo -e "${YELLOW}Step 6: Copying project files...${NC}"

# Copy backend (excluding temp and cache)
rsync -avz --delete \
    --exclude='temp/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='app/' \
    --exclude='config/' \
    -e "ssh -i $SSH_KEY" \
    ./backend/ "$EC2_USER@$EC2_HOST:$REMOTE_DIR/backend/"

# Copy frontend
rsync -avz --delete \
    --exclude='.DS_Store' \
    -e "ssh -i $SSH_KEY" \
    ./frontend/ "$EC2_USER@$EC2_HOST:$REMOTE_DIR/frontend/"

# Copy CLI
rsync -avz --delete \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    -e "ssh -i $SSH_KEY" \
    ./cli/ "$EC2_USER@$EC2_HOST:$REMOTE_DIR/cli/"

# Step 7: Install Python dependencies
echo -e "${YELLOW}Step 7: Installing Python dependencies...${NC}"
run_remote "cd $REMOTE_DIR && source venv/bin/activate && pip install --upgrade pip"
run_remote "cd $REMOTE_DIR && source venv/bin/activate && pip install -r backend/requirements.txt"

# Step 8: Create temp directory and set permissions
echo -e "${YELLOW}Step 8: Setting up directories and permissions...${NC}"
run_remote "mkdir -p $REMOTE_DIR/backend/temp"
run_remote "chmod 755 $REMOTE_DIR/backend/temp"
run_remote "chown -R ubuntu:ubuntu $REMOTE_DIR"

# Step 9: Create systemd service
echo -e "${YELLOW}Step 9: Creating systemd service...${NC}"
cat <<'EOF' | ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "sudo tee /etc/systemd/system/bodyscript.service > /dev/null"
[Unit]
Description=BodyScript Pose Detection API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bodyscript/backend
Environment="PATH=/home/ubuntu/bodyscript/venv/bin"
Environment="PYTHONPATH=/home/ubuntu/bodyscript"
Environment="ENVIRONMENT=production"
ExecStart=/home/ubuntu/bodyscript/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=10

# Resource limits for t2.micro
MemoryMax=768M
CPUQuota=90%

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Step 10: Create production environment file
echo -e "${YELLOW}Step 10: Creating production environment...${NC}"
cat <<'EOF' | ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "tee $REMOTE_DIR/.env.production > /dev/null"
ENVIRONMENT=production
MAX_VIDEO_SIZE_MB=30
MAX_VIDEO_DURATION=10
MEMORY_LIMIT_MB=400
ADMIN_TOKEN=your_admin_token_here
# Add R2 credentials if using cloud storage
# R2_ACCOUNT_ID=
# R2_ACCESS_KEY=
# R2_SECRET_KEY=
EOF

# Step 11: Update Nginx configuration for native deployment
echo -e "${YELLOW}Step 11: Verifying Nginx configuration...${NC}"
run_remote "sudo nginx -t"

# Step 12: Start and enable the service
echo -e "${YELLOW}Step 12: Starting BodyScript service...${NC}"
run_remote "sudo systemctl daemon-reload"
run_remote "sudo systemctl enable bodyscript"
run_remote "sudo systemctl restart bodyscript"

# Step 13: Verify service is running
echo -e "${YELLOW}Step 13: Verifying service status...${NC}"
sleep 3
run_remote "sudo systemctl status bodyscript --no-pager"

# Step 14: Test the API
echo -e "${YELLOW}Step 14: Testing API endpoint...${NC}"
sleep 2
if curl -s -o /dev/null -w "%{http_code}" "http://$EC2_HOST/health" | grep -q "200"; then
    echo -e "${GREEN}✅ API is responding correctly!${NC}"
else
    echo -e "${RED}⚠️  API is not responding. Check logs with:${NC}"
    echo "ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'sudo journalctl -u bodyscript -n 50'"
fi

# Step 15: Clean up Docker (optional)
echo -e "${YELLOW}Step 15: Docker cleanup...${NC}"
echo -e "Do you want to remove Docker images to free up space? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    run_remote "sudo docker system prune -a -f"
    echo -e "${GREEN}Docker images removed${NC}"
else
    echo "Keeping Docker images"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Service Status: ${GREEN}Running${NC}"
echo -e "URL: ${GREEN}http://$EC2_HOST${NC}"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View logs:    ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'sudo journalctl -u bodyscript -f'"
echo "  Restart:      ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'sudo systemctl restart bodyscript'"
echo "  Deploy code:  ./scripts/deploy-native.sh"
echo ""