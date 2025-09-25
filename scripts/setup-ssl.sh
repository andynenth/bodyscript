#!/bin/bash

# SSL Setup Script for BodyScript
# Supports both Let's Encrypt (with domain) and self-signed certificates

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
echo -e "${GREEN}  SSL Setup for BodyScript${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to run commands on EC2
run_remote() {
    ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "$1"
}

# Check if user has a domain
echo -e "${YELLOW}Do you have a domain name pointing to $EC2_HOST? (y/n)${NC}"
read -r has_domain

if [[ "$has_domain" =~ ^[Yy]$ ]]; then
    # Let's Encrypt setup
    echo -e "${BLUE}Enter your domain name (e.g., bodyscript.example.com):${NC}"
    read -r DOMAIN_NAME

    echo -e "${BLUE}Enter your email for Let's Encrypt notifications:${NC}"
    read -r EMAIL

    echo -e "${YELLOW}Setting up Let's Encrypt SSL for $DOMAIN_NAME...${NC}"

    # Step 1: Install Certbot
    echo -e "${YELLOW}Step 1: Installing Certbot...${NC}"
    run_remote "sudo apt-get update && sudo apt-get install -y certbot python3-certbot-nginx"

    # Step 2: Update Nginx configuration with domain
    echo -e "${YELLOW}Step 2: Updating Nginx configuration...${NC}"
    cat <<EOF | ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "sudo tee /etc/nginx/sites-available/bodyscript > /dev/null"
# BodyScript Nginx Configuration with SSL
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN_NAME;

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }

    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN_NAME;

    # SSL certificates will be added by Certbot
    # ssl_certificate /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Upload size for videos
    client_max_body_size 50M;
    client_body_timeout 300s;

    # API backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeouts for video processing
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
    }

    # Upload endpoint
    location /upload {
        proxy_pass http://localhost:8000/upload;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Extended timeouts for upload
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Processed videos
    location /temp/ {
        proxy_pass http://localhost:8000/temp/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Frontend static files
    location / {
        root /home/ubuntu/bodyscript/frontend;
        try_files \$uri \$uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # Frontend assets
    location /assets/ {
        root /home/ubuntu/bodyscript/frontend;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    location /css/ {
        root /home/ubuntu/bodyscript/frontend;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    location /js/ {
        root /home/ubuntu/bodyscript/frontend;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Step 3: Test and reload Nginx
    echo -e "${YELLOW}Step 3: Testing Nginx configuration...${NC}"
    run_remote "sudo nginx -t && sudo systemctl reload nginx"

    # Step 4: Obtain SSL certificate
    echo -e "${YELLOW}Step 4: Obtaining SSL certificate from Let's Encrypt...${NC}"
    run_remote "sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email $EMAIL"

    # Step 5: Set up auto-renewal
    echo -e "${YELLOW}Step 5: Setting up auto-renewal...${NC}"
    run_remote "sudo systemctl enable certbot.timer && sudo systemctl start certbot.timer"

    # Step 6: Test renewal
    echo -e "${YELLOW}Step 6: Testing certificate renewal...${NC}"
    run_remote "sudo certbot renew --dry-run"

    echo -e "${GREEN}✅ SSL setup complete!${NC}"
    echo -e "${GREEN}Your site is now available at: https://$DOMAIN_NAME${NC}"

else
    # Self-signed certificate setup
    echo -e "${YELLOW}Setting up self-signed SSL certificate...${NC}"
    echo -e "${RED}Note: Browsers will show a security warning with self-signed certificates${NC}"

    # Step 1: Generate self-signed certificate
    echo -e "${YELLOW}Step 1: Generating self-signed certificate...${NC}"
    run_remote "sudo mkdir -p /etc/ssl/bodyscript"
    run_remote "sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/bodyscript/bodyscript.key \
        -out /etc/ssl/bodyscript/bodyscript.crt \
        -subj '/C=US/ST=State/L=City/O=BodyScript/CN=$EC2_HOST'"

    # Step 2: Update Nginx configuration
    echo -e "${YELLOW}Step 2: Updating Nginx configuration...${NC}"
    cat <<EOF | ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "sudo tee /etc/nginx/sites-available/bodyscript > /dev/null"
# BodyScript Nginx Configuration with Self-Signed SSL
server {
    listen 80;
    listen [::]:80;
    server_name _;

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;

    # Self-signed SSL certificates
    ssl_certificate /etc/ssl/bodyscript/bodyscript.crt;
    ssl_certificate_key /etc/ssl/bodyscript/bodyscript.key;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Upload size for videos
    client_max_body_size 50M;
    client_body_timeout 300s;

    # API backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeouts for video processing
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
    }

    # Upload endpoint
    location /upload {
        proxy_pass http://localhost:8000/upload;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Extended timeouts for upload
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Processed videos
    location /temp/ {
        proxy_pass http://localhost:8000/temp/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Frontend static files
    location / {
        root /home/ubuntu/bodyscript/frontend;
        try_files \$uri \$uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # Frontend assets
    location /assets/ {
        root /home/ubuntu/bodyscript/frontend;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    location /css/ {
        root /home/ubuntu/bodyscript/frontend;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    location /js/ {
        root /home/ubuntu/bodyscript/frontend;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Step 3: Test and reload Nginx
    echo -e "${YELLOW}Step 3: Testing and reloading Nginx...${NC}"
    run_remote "sudo nginx -t && sudo systemctl reload nginx"

    echo -e "${GREEN}✅ Self-signed SSL setup complete!${NC}"
    echo -e "${YELLOW}Your site is now available at: https://$EC2_HOST${NC}"
    echo -e "${RED}Note: You'll see a browser warning about the certificate${NC}"
fi

# Step 7: Update EC2 Security Group reminder
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  IMPORTANT: EC2 Security Group${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "${BLUE}Make sure your EC2 security group allows:${NC}"
echo "  • Port 443 (HTTPS) from 0.0.0.0/0"
echo "  • Port 80 (HTTP) from 0.0.0.0/0"
echo ""
echo -e "${BLUE}To update via AWS CLI:${NC}"
echo "aws ec2 authorize-security-group-ingress \\"
echo "  --group-id YOUR_SECURITY_GROUP_ID \\"
echo "  --protocol tcp --port 443 --cidr 0.0.0.0/0"
echo ""

# Test HTTPS
echo -e "${YELLOW}Testing HTTPS connection...${NC}"
if [[ "$has_domain" =~ ^[Yy]$ ]]; then
    curl -s -o /dev/null -w "HTTPS Status: %{http_code}\n" "https://$DOMAIN_NAME/health" || echo -e "${RED}Connection failed - check security group${NC}"
else
    curl -k -s -o /dev/null -w "HTTPS Status: %{http_code}\n" "https://$EC2_HOST/health" || echo -e "${RED}Connection failed - check security group${NC}"
fi