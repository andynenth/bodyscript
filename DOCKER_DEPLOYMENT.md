# Docker Deployment Guide for BodyScript

## Overview

This guide covers deploying BodyScript using Docker, both locally and on AWS EC2.

## Quick Start

### Local Development

```bash
# Test Docker setup
./scripts/test-docker-local.sh

# Run locally
./scripts/deploy-local.sh
```

Access at: `http://localhost:8000`

### EC2 Production Deployment

```bash
# On EC2 instance
./scripts/setup-ec2.sh

# Deploy application
./scripts/deploy-ec2.sh
```

Access at: `http://bodyscript.andynenth.dev:8000`

## Architecture

- **Single Container**: FastAPI serves both API and frontend
- **Memory Optimized**: Multi-stage build, slim base image
- **Environment-based Config**: Different settings for local/production
- **Fallback Option**: Can switch to native if Docker uses too much memory

## File Structure

```
bodyscript/
├── docker-compose.yml       # Main compose file
├── .env.local              # Local environment
├── .env.production         # Production environment
├── backend/
│   ├── Dockerfile          # Optimized multi-stage build
│   └── .dockerignore       # Exclude unnecessary files
├── frontend/
│   └── config.js           # Auto-detects environment
└── scripts/
    ├── deploy-local.sh     # Local deployment
    ├── deploy-ec2.sh       # EC2 deployment
    ├── setup-ec2.sh        # EC2 initial setup
    ├── monitor.sh          # Memory monitoring
    └── switch-to-native.sh # Fallback to native

```

## Environment Variables

### Local (.env.local)
- `ENVIRONMENT=development`
- `APP_PORT=8000`
- `MEMORY_LIMIT=800m`
- Hot reload enabled

### Production (.env.production)
- `ENVIRONMENT=production`
- `APP_PORT=8000`
- `MEMORY_LIMIT=750m`
- Auto-restart enabled
- **IMPORTANT**: Change `ADMIN_TOKEN` before deploying!

## EC2 Setup Steps

### 1. Launch EC2 Instance
- AMI: Ubuntu 22.04 LTS
- Type: t2.micro (free tier)
- Security Group: Open ports 22, 8000
- Assign Elastic IP

### 2. Initial Setup
```bash
# SSH to instance
ssh ubuntu@your-ec2-ip

# Clone repository
git clone https://github.com/yourusername/bodyscript.git
cd bodyscript

# Run setup
./scripts/setup-ec2.sh

# Logout and login for Docker permissions
exit
ssh ubuntu@your-ec2-ip
```

### 3. Configure Environment
```bash
# Copy and edit production environment
cp .env.production.template .env.production
nano .env.production

# Set your admin token and any R2 credentials
```

### 4. Deploy Application
```bash
./scripts/deploy-ec2.sh
```

### 5. Monitor Memory
```bash
# In another terminal
./scripts/monitor.sh
```

## Memory Management

### Monitoring
The monitor script alerts when memory usage exceeds 80%.

### If Memory Issues Occur
```bash
# Quick switch to native installation
./scripts/switch-to-native.sh
```

This will:
1. Stop Docker containers
2. Install Python dependencies natively
3. Create systemd service
4. Run FastAPI directly (saves ~250MB RAM)

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose --env-file .env.local logs

# Check memory
docker stats
```

### High memory usage
```bash
# Check what's using memory
docker exec bodyscript-bodyscript-1 ps aux

# Restart to clear memory
docker-compose --env-file .env.production restart
```

### Can't access from browser
```bash
# Check if running
docker ps

# Check health
curl http://localhost:8000/health

# Check EC2 security group
# Ensure port 8000 is open
```

## Clean URLs

Currently serves at port 8000. To get clean URLs without port:

1. **Option A**: Use nginx reverse proxy (adds complexity)
2. **Option B**: Use Application Load Balancer (costs money)
3. **Option C**: Accept port in URL (simplest)

## Maintenance

### Update application
```bash
git pull
./scripts/deploy-ec2.sh
```

### Backup data
```bash
# Backup temp files if needed
docker cp bodyscript-bodyscript-1:/app/temp ./backup
```

### View logs
```bash
docker-compose logs -f --tail=100
```

## Performance Tips

1. **Video limits**: Keep videos under 30MB and 10 seconds
2. **Memory spikes**: Normal during video processing
3. **Swap space**: 2GB swap helps prevent OOM crashes
4. **Monitoring**: Run monitor.sh to track usage

## Security Notes

1. **Change ADMIN_TOKEN** in production
2. **Use HTTPS** in production (add nginx + certbot)
3. **Firewall**: Only open necessary ports
4. **Updates**: Keep system and Docker updated

## Support

If issues persist:
1. Check logs: `docker-compose logs`
2. Monitor memory: `docker stats`
3. Try native installation: `./scripts/switch-to-native.sh`
4. Check system resources: `free -h`, `df -h`