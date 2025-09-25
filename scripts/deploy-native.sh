#!/bin/bash

# Quick Deploy Script for BodyScript (Native)
# This script syncs code changes to EC2 and restarts the service

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
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}Error: SSH key not found at $SSH_KEY${NC}"
    echo "Please ensure your SSH key is at the correct location"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deploying Code to EC2${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to run commands on EC2
run_remote() {
    ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "$1"
}

# Step 1: Sync Backend Code
echo -e "${YELLOW}Step 1: Syncing backend code...${NC}"
rsync -avz --progress \
    --exclude='temp/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='.env.local' \
    --exclude='app/' \
    --exclude='config/' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    -e "ssh -i $SSH_KEY" \
    ./backend/ "$EC2_USER@$EC2_HOST:$REMOTE_DIR/backend/"

echo -e "${GREEN}✅ Backend code synced${NC}"

# Step 2: Sync Frontend Code
echo -e "${YELLOW}Step 2: Syncing frontend code...${NC}"
rsync -avz --progress \
    --exclude='.DS_Store' \
    --exclude='*.log' \
    -e "ssh -i $SSH_KEY" \
    ./frontend/ "$EC2_USER@$EC2_HOST:$REMOTE_DIR/frontend/"

echo -e "${GREEN}✅ Frontend code synced${NC}"

# Step 3: Sync CLI Code (if changed)
echo -e "${YELLOW}Step 3: Syncing CLI code...${NC}"
rsync -avz --progress \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    -e "ssh -i $SSH_KEY" \
    ./cli/ "$EC2_USER@$EC2_HOST:$REMOTE_DIR/cli/"

echo -e "${GREEN}✅ CLI code synced${NC}"

# Step 4: Check if requirements changed
echo -e "${YELLOW}Step 4: Checking dependencies...${NC}"
if ! ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "diff -q $REMOTE_DIR/backend/requirements.txt /tmp/last_requirements.txt 2>/dev/null"; then
    echo -e "${BLUE}Dependencies changed, updating...${NC}"
    run_remote "cd $REMOTE_DIR && source venv/bin/activate && pip install -r backend/requirements.txt"
    run_remote "cp $REMOTE_DIR/backend/requirements.txt /tmp/last_requirements.txt"
    echo -e "${GREEN}✅ Dependencies updated${NC}"
else
    echo -e "${GREEN}✅ No dependency changes${NC}"
fi

# Step 5: Restart the service
echo -e "${YELLOW}Step 5: Restarting BodyScript service...${NC}"
run_remote "sudo systemctl restart bodyscript"

# Step 6: Wait for service to start
echo -e "${YELLOW}Step 6: Waiting for service to start...${NC}"
sleep 3

# Step 7: Check service status
echo -e "${YELLOW}Step 7: Checking service status...${NC}"
if run_remote "sudo systemctl is-active bodyscript" | grep -q "active"; then
    echo -e "${GREEN}✅ Service is running${NC}"
else
    echo -e "${RED}⚠️  Service failed to start${NC}"
    echo -e "${YELLOW}Recent logs:${NC}"
    run_remote "sudo journalctl -u bodyscript -n 20 --no-pager"
    exit 1
fi

# Step 8: Test the API
echo -e "${YELLOW}Step 8: Testing API endpoint...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$EC2_HOST/health")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ API is responding (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}⚠️  API returned HTTP $HTTP_CODE${NC}"
    echo -e "${YELLOW}Recent logs:${NC}"
    run_remote "sudo journalctl -u bodyscript -n 20 --no-pager"
fi

# Step 9: Show deployment summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "🌐 URL: ${GREEN}http://$EC2_HOST${NC}"
echo -e "📊 Status: $(run_remote 'sudo systemctl is-active bodyscript')"
echo -e "💾 Memory: $(run_remote 'free -h | grep Mem | awk "{print \$3 \"/\" \$2}"')"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo "  ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'sudo journalctl -u bodyscript -f'"
echo ""