#!/bin/bash
# Quick switch from Docker to native if memory issues

echo "🔄 Switching from Docker to native installation..."

# Stop Docker containers
echo "🛑 Stopping Docker containers..."
docker-compose down

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd backend
pip3 install --user -r requirements.txt

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/bodyscript.service > /dev/null <<EOF
[Unit]
Description=BodyScript API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bodyscript/backend
Environment="PATH=/home/ubuntu/.local/bin:/usr/bin"
EnvironmentFile=/home/ubuntu/bodyscript/.env.production
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start native service
echo "🏃 Starting native service..."
sudo systemctl daemon-reload
sudo systemctl enable bodyscript
sudo systemctl start bodyscript

# Wait for service to start
sleep 5

# Check status
if sudo systemctl is-active --quiet bodyscript; then
    echo "✅ Successfully switched to native installation!"
    echo ""
    echo "Service status:"
    sudo systemctl status bodyscript --no-pager
    echo ""
    echo "📊 Memory usage:"
    ps aux | grep python3 | grep app.py
    echo ""
    echo "🌐 Access at: http://$(curl -s ifconfig.me):8000"
else
    echo "❌ Failed to start native service"
    echo "Check logs with: sudo journalctl -u bodyscript -n 50"
    exit 1
fi