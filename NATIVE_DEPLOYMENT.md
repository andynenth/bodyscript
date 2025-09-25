# Native Deployment Workflow for BodyScript

## Overview
Native deployment runs the Python application directly on EC2 without Docker, reducing overhead and complexity for resource-constrained t2.micro instances.

## Architecture
```
[Local Machine] ---(rsync)---> [EC2 Instance]
     |                              |
  Development                    Production
  - Code editing                - Python 3.9
  - Testing                     - Systemd service
  - Git commits                 - Nginx (already set)
```

## What Happens Where

### 🖥️ LOCAL MACHINE Tasks

1. **Development**
   - Write and test code locally
   - Run `python -m uvicorn app:app --port 8000` for testing
   - Commit changes to git

2. **Before Deployment**
   - Ensure code works locally
   - Check that `backend/requirements.txt` is up to date
   - Verify no hardcoded paths that won't work on EC2

3. **Deployment Commands**
   ```bash
   # Quick sync (code only)
   ./scripts/deploy-native.sh

   # Full setup (first time or after EC2 restart)
   ./scripts/setup-ec2-native.sh

   # Update dependencies
   ./scripts/update-ec2-deps.sh
   ```

### 🌐 EC2 INSTANCE Setup

1. **Directory Structure**
   ```
   /home/ubuntu/bodyscript/
   ├── backend/          # Python application
   │   ├── app.py
   │   ├── requirements.txt
   │   └── temp/         # Processed videos
   ├── frontend/         # Static files (Nginx serves)
   ├── cli/             # CLI tools
   └── venv/            # Python virtual environment
   ```

2. **Services Running**
   - **Nginx**: Port 80 → Serves frontend, proxies /api to port 8000
   - **BodyScript**: Port 8000 → Python FastAPI application
   - **Systemd**: Manages bodyscript.service

3. **Data Persistence**
   - `/home/ubuntu/bodyscript/backend/temp/` - Processed videos persist
   - No Docker volumes needed

## Deployment Workflow

### First-Time Setup (One-time on new EC2)

1. **Run locally:**
   ```bash
   ./scripts/setup-ec2-native.sh
   ```
   This script will SSH to EC2 and:
   - Install Python 3.9 and system dependencies
   - Create virtual environment
   - Install Python packages
   - Set up systemd service
   - Configure file permissions
   - Start the service

### Regular Code Updates

1. **Test locally first:**
   ```bash
   cd backend
   python -m uvicorn app:app --port 8000
   # Test at http://localhost:8000
   ```

2. **Deploy to EC2:**
   ```bash
   ./scripts/deploy-native.sh
   ```
   This will:
   - Sync code files (excluding temp/, venv/, __pycache__)
   - Restart the service
   - Show service status

### Updating Dependencies

When you add new packages to requirements.txt:

1. **Update locally:**
   ```bash
   pip install new-package
   pip freeze > backend/requirements.txt
   ```

2. **Deploy with dependencies:**
   ```bash
   ./scripts/update-ec2-deps.sh
   ```

## File Sync Strategy

### What Gets Synced
- ✅ Python files (*.py)
- ✅ Frontend files (HTML, CSS, JS)
- ✅ Configuration files
- ✅ requirements.txt

### What Doesn't Sync
- ❌ backend/temp/ (processed videos)
- ❌ venv/ (Python environment)
- ❌ __pycache__/ (Python cache)
- ❌ .git/ (version control)
- ❌ *.pyc files
- ❌ .env files (security)

## Service Management

### Check Status
```bash
ssh -i ~/.ssh/bodyscript-key.pem ubuntu@98.81.229.113 \
  'sudo systemctl status bodyscript'
```

### View Logs
```bash
# Recent logs
ssh -i ~/.ssh/bodyscript-key.pem ubuntu@98.81.229.113 \
  'sudo journalctl -u bodyscript -n 50'

# Follow logs
ssh -i ~/.ssh/bodyscript-key.pem ubuntu@98.81.229.113 \
  'sudo journalctl -u bodyscript -f'
```

### Restart Service
```bash
ssh -i ~/.ssh/bodyscript-key.pem ubuntu@98.81.229.113 \
  'sudo systemctl restart bodyscript'
```

## Environment Variables

Create `/home/ubuntu/bodyscript/.env.production` on EC2:
```bash
ENVIRONMENT=production
MAX_VIDEO_SIZE_MB=30
MAX_VIDEO_DURATION=10
MEMORY_LIMIT_MB=400
# Add R2 credentials if using cloud storage
```

## Troubleshooting

### Service Won't Start
1. Check logs: `sudo journalctl -u bodyscript -n 100`
2. Check Python path: `which python3`
3. Test manually: `cd /home/ubuntu/bodyscript && venv/bin/python backend/app.py`

### Import Errors
1. Activate venv: `source /home/ubuntu/bodyscript/venv/bin/activate`
2. Check installed packages: `pip list`
3. Reinstall requirements: `pip install -r backend/requirements.txt`

### Permission Errors
1. Check ownership: `ls -la /home/ubuntu/bodyscript/`
2. Fix permissions: `sudo chown -R ubuntu:ubuntu /home/ubuntu/bodyscript/`
3. Fix temp directory: `chmod 755 /home/ubuntu/bodyscript/backend/temp/`

### High Memory Usage
1. Check process: `top` or `htop`
2. Restart service: `sudo systemctl restart bodyscript`
3. Check for memory leaks in video processing

## Advantages Over Docker

1. **Resource Efficiency**
   - No Docker daemon overhead (~100MB RAM saved)
   - No container layer overhead
   - Direct file access (no volume mounting)

2. **Deployment Speed**
   - Sync only changed files (seconds vs minutes)
   - No image building
   - No image transfer

3. **Debugging**
   - Direct access to Python process
   - Standard Linux tools work directly
   - Easier log access

4. **Storage**
   - No Docker image storage (save 1GB+)
   - Direct file system access
   - Easier backup/restore

## Migration from Docker

To switch from Docker to native:

1. **Stop Docker containers:**
   ```bash
   ssh -i ~/.ssh/bodyscript-key.pem ubuntu@98.81.229.113 \
     'sudo docker stop bodyscript-api && sudo docker-compose down'
   ```

2. **Backup data (if needed):**
   ```bash
   ssh -i ~/.ssh/bodyscript-key.pem ubuntu@98.81.229.113 \
     'sudo docker cp bodyscript-api:/app/temp /home/ubuntu/bodyscript/backend/'
   ```

3. **Run native setup:**
   ```bash
   ./scripts/setup-ec2-native.sh
   ```

4. **Clean up Docker (optional):**
   ```bash
   ssh -i ~/.ssh/bodyscript-key.pem ubuntu@98.81.229.113 \
     'sudo docker system prune -a'
   ```