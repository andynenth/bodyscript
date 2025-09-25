#!/bin/bash

# Update Dependencies Script for EC2 Native Deployment
# Use this when you've added new packages to requirements.txt

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
echo -e "${GREEN}  Updating EC2 Dependencies${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to run commands on EC2
run_remote() {
    ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "$1"
}

# Step 1: Copy new requirements.txt
echo -e "${YELLOW}Step 1: Copying requirements.txt...${NC}"
scp -i "$SSH_KEY" ./backend/requirements.txt "$EC2_USER@$EC2_HOST:$REMOTE_DIR/backend/"
echo -e "${GREEN}✅ requirements.txt copied${NC}"

# Step 2: Show what will be installed/updated
echo -e "${YELLOW}Step 2: Checking for package changes...${NC}"
echo "Current requirements:"
cat ./backend/requirements.txt
echo ""

# Step 3: Update pip
echo -e "${YELLOW}Step 3: Updating pip...${NC}"
run_remote "cd $REMOTE_DIR && source venv/bin/activate && pip install --upgrade pip"

# Step 4: Install new dependencies
echo -e "${YELLOW}Step 4: Installing dependencies...${NC}"
run_remote "cd $REMOTE_DIR && source venv/bin/activate && pip install -r backend/requirements.txt"

# Step 5: Show installed packages
echo -e "${YELLOW}Step 5: Verifying installation...${NC}"
echo "Installed packages:"
run_remote "cd $REMOTE_DIR && source venv/bin/activate && pip list | head -20"
echo "..."
echo -e "${GREEN}✅ Dependencies updated${NC}"

# Step 6: Restart service
echo -e "${YELLOW}Step 6: Restarting BodyScript service...${NC}"
run_remote "sudo systemctl restart bodyscript"
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
echo -e "${YELLOW}Step 8: Testing API...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "http://$EC2_HOST/health" | grep -q "200"; then
    echo -e "${GREEN}✅ API is responding correctly${NC}"
else
    echo -e "${RED}⚠️  API is not responding${NC}"
    echo -e "${YELLOW}Check logs with:${NC}"
    echo "ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'sudo journalctl -u bodyscript -n 50'"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Dependencies Updated Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"