#!/bin/bash

# Setup Admin Token for BodyScript Production
# This script configures the admin authentication token on EC2

set -e  # Exit on error

# Configuration
EC2_HOST="98.81.229.113"
EC2_USER="ubuntu"
SSH_KEY="$HOME/.ssh/bodyscript-key.pem"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}Error: SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Admin Token Setup for BodyScript${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Generate a secure random token
generate_token() {
    openssl rand -hex 32
}

# Ask user for token choice
echo -e "${YELLOW}Choose an option:${NC}"
echo "1) Generate a secure random token (recommended)"
echo "2) Enter your own custom token"
echo ""
read -p "Your choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    ADMIN_TOKEN=$(generate_token)
    echo -e "${GREEN}Generated secure token:${NC} $ADMIN_TOKEN"
elif [ "$choice" = "2" ]; then
    echo -e "${BLUE}Enter your custom admin token (make it strong!):${NC}"
    read -s ADMIN_TOKEN
    echo ""
else
    echo -e "${RED}Invalid choice${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Setting up admin token on EC2...${NC}"

# SSH to EC2 and set up the environment variable
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
# Create environment file for systemd service
echo "Creating environment configuration..."
sudo tee /home/ubuntu/bodyscript/backend/.env > /dev/null << 'EOV'
ADMIN_TOKEN=$ADMIN_TOKEN
ENVIRONMENT=production
EOV

# Set proper permissions
sudo chown ubuntu:ubuntu /home/ubuntu/bodyscript/backend/.env
chmod 600 /home/ubuntu/bodyscript/backend/.env

# Update systemd service to use environment file
echo "Updating systemd service..."
sudo tee /etc/systemd/system/bodyscript.service > /dev/null << 'EOS'
[Unit]
Description=BodyScript Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bodyscript/backend
EnvironmentFile=/home/ubuntu/bodyscript/backend/.env
ExecStart=/home/ubuntu/bodyscript/venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOS

# Reload and restart the service
echo "Restarting backend service..."
sudo systemctl daemon-reload
sudo systemctl restart bodyscript
sudo systemctl status bodyscript --no-pager

echo "Admin token configured successfully!"
EOF

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT: Save your admin token securely!${NC}"
echo -e "${BLUE}Admin Token:${NC} $ADMIN_TOKEN"
echo ""
echo -e "${YELLOW}To access admin features:${NC}"
echo "1. Go to: https://bodyscript.andynenth.dev/admin.html"
echo "2. Enter your admin token when prompted"
echo ""
echo -e "${YELLOW}Or use the API directly:${NC}"
echo "curl https://bodyscript.andynenth.dev/admin/pending-videos?auth=YOUR_TOKEN"
echo ""
echo -e "${GREEN}The token has been set on the EC2 instance.${NC}"
echo -e "${RED}Keep this token safe and don't share it!${NC}"