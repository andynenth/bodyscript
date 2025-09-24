#!/bin/bash
set -e

echo "🔧 Setting up EC2 instance for BodyScript..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "🐋 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    rm get-docker.sh
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "🐋 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo apt-get install -y docker-compose
else
    echo "Docker Compose already installed"
fi

# Setup swap (critical for t2.micro)
echo "💾 Setting up swap space..."
if [ ! -f /swapfile ]; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "Swap created: 2GB"
else
    echo "Swap already exists"
fi

# Configure Docker memory limits and logging
echo "⚙️ Configuring Docker daemon..."
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "memlock": {
      "Name": "memlock",
      "Hard": -1,
      "Soft": -1
    }
  }
}
EOF

sudo systemctl restart docker

# Setup firewall
echo "🔒 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw --force enable

# Create app directory
echo "📁 Creating application directory..."
mkdir -p ~/bodyscript

# Install Git if not present
if ! command -v git &> /dev/null; then
    sudo apt-get install -y git
fi

echo "✅ EC2 setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone your repository: git clone <your-repo-url> ~/bodyscript"
echo "2. Navigate to project: cd ~/bodyscript"
echo "3. Copy .env.production file and set your secrets"
echo "4. Run deployment: ./scripts/deploy-ec2.sh"
echo ""
echo "⚠️ Please logout and login again for Docker group permissions to take effect"