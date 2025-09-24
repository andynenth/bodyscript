#!/bin/bash

# BodyScript Production Deployment Script
# This script handles deployment to production with enhanced safety checks and monitoring

set -euo pipefail

# Configuration
PRODUCTION_BRANCH="main"
PRODUCTION_URL="https://bodyscript.com"
PRODUCTION_API_URL="https://api.bodyscript.com"
BACKUP_DIR="/backup/bodyscript-$(date +%Y%m%d_%H%M%S)"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
DEPLOYMENT_LOG="/var/log/bodyscript/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${BLUE}$message${NC}"
    echo "$message" >> "$DEPLOYMENT_LOG"
}

success() {
    local message="[SUCCESS] $1"
    echo -e "${GREEN}$message${NC}"
    echo "$message" >> "$DEPLOYMENT_LOG"
}

warning() {
    local message="[WARNING] $1"
    echo -e "${YELLOW}$message${NC}"
    echo "$message" >> "$DEPLOYMENT_LOG"
}

error() {
    local message="[ERROR] $1"
    echo -e "${RED}$message${NC}"
    echo "$message" >> "$DEPLOYMENT_LOG"
    send_slack_notification "🔴 Production deployment failed: $1"
    exit 1
}

# Slack notification function
send_slack_notification() {
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$1\"}" \
            "$SLACK_WEBHOOK_URL" || true
    fi
}

# Enhanced pre-deployment checks for production
pre_deployment_checks() {
    log "Running enhanced pre-deployment checks for production..."

    # Check if we're on the production branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$PRODUCTION_BRANCH" ]; then
        error "Must be on production branch ($PRODUCTION_BRANCH). Current: $current_branch"
    fi

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        error "Uncommitted changes detected. Please commit changes first."
    fi

    # Verify we're ahead of current production
    if ! git merge-base --is-ancestor origin/main HEAD; then
        error "Current HEAD is not ahead of origin/main"
    fi

    # Check if production environment variables exist
    if [ ! -f ".env.production" ]; then
        error "Production environment file (.env.production) not found"
    fi

    # Check required environment variables
    source .env.production
    required_vars=("DATABASE_URL" "SECRET_KEY" "MEDIAPIPE_LICENSE" "STORAGE_BUCKET")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            error "Required environment variable $var is not set"
        fi
    done

    # Check system resources
    available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [ "$available_memory" -lt 1000 ]; then
        warning "Available memory is low: ${available_memory}MB"
    fi

    available_disk=$(df / | awk 'NR==2{print $4}')
    if [ "$available_disk" -lt 5000000 ]; then
        warning "Available disk space is low: ${available_disk}KB"
    fi

    # Check Node.js and Python versions match requirements
    node_version=$(node --version | sed 's/v//')
    required_node="18.0.0"
    if ! node -e "process.exit(require('semver').gte('$node_version', '$required_node') ? 0 : 1)" 2>/dev/null; then
        error "Node.js version $node_version does not meet minimum requirement: $required_node"
    fi

    python_version=$(python3 --version | cut -d' ' -f2)
    required_python="3.9.0"
    if ! python3 -c "import sys; exit(0 if tuple(map(int, sys.version.split()[0].split('.'))) >= tuple(map(int, '$required_python'.split('.'))) else 1)"; then
        error "Python version $python_version does not meet minimum requirement: $required_python"
    fi

    success "Enhanced pre-deployment checks passed"
}

# Create comprehensive backup
create_backup() {
    log "Creating comprehensive backup..."
    sudo mkdir -p "$BACKUP_DIR"

    # Backup current deployment
    if [ -d "/var/www/bodyscript" ]; then
        sudo tar -czf "$BACKUP_DIR/deployment.tar.gz" /var/www/bodyscript
        success "Application backup created"
    fi

    # Backup database
    if command -v pg_dump &> /dev/null; then
        sudo -u postgres pg_dump bodyscript > "$BACKUP_DIR/database.sql"
        success "Database backup created"
    fi

    # Backup configuration
    sudo cp /etc/nginx/sites-available/bodyscript "$BACKUP_DIR/nginx.conf"
    sudo cp /etc/systemd/system/bodyscript-api.service "$BACKUP_DIR/systemd.service"

    success "Comprehensive backup completed at $BACKUP_DIR"
}

# Install and audit dependencies
install_dependencies() {
    log "Installing and auditing dependencies..."

    # Install Node.js dependencies with security audit
    npm ci --production=false
    npm audit --audit-level high

    # Install Python dependencies with security check
    pip install --upgrade pip
    pip install -r backend/requirements.txt
    pip install safety
    safety check --ignore 40291  # Ignore known false positives

    success "Dependencies installed and audited"
}

# Comprehensive test suite
run_comprehensive_tests() {
    log "Running comprehensive test suite..."

    # Frontend tests with coverage
    npm run test:unit -- --coverage
    npm run test:integration
    npm run lint
    npm run type-check

    # Backend tests with coverage
    cd backend
    python -m pytest tests/ -v --cov=. --cov-report=html
    python -m pytest tests/integration/ -v
    cd ..

    # End-to-end tests
    npm run test:e2e

    # Performance tests
    npm run test:performance

    success "Comprehensive test suite passed"
}

# Build for production
build_production() {
    log "Building for production..."

    # Set production environment
    export NODE_ENV=production
    cp .env.production .env

    # Build frontend with optimization
    npm run build:prod

    # Build and optimize Python package
    cd backend
    python setup.py build_ext --inplace
    python -m py_compile $(find . -name "*.py")
    cd ..

    # Generate build manifest
    echo "BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > build-info.txt
    echo "GIT_COMMIT=$(git rev-parse HEAD)" >> build-info.txt
    echo "GIT_BRANCH=$(git branch --show-current)" >> build-info.txt

    success "Production build completed"
}

# Blue-green deployment
deploy_blue_green() {
    log "Performing blue-green deployment..."

    # Determine current and new deployment directories
    if [ -L "/var/www/bodyscript-current" ] && [ -d "/var/www/bodyscript-blue" ]; then
        NEW_ENV="green"
        OLD_ENV="blue"
    else
        NEW_ENV="blue"
        OLD_ENV="green"
    fi

    NEW_DIR="/var/www/bodyscript-$NEW_ENV"
    OLD_DIR="/var/www/bodyscript-$OLD_ENV"

    log "Deploying to $NEW_ENV environment"

    # Create new deployment directory
    sudo mkdir -p "$NEW_DIR"

    # Copy built files
    sudo cp -r frontend/dist/* "$NEW_DIR/"
    sudo cp -r backend "$NEW_DIR/"
    sudo cp .env.production "$NEW_DIR/.env"
    sudo cp build-info.txt "$NEW_DIR/"

    # Set proper permissions
    sudo chown -R www-data:www-data "$NEW_DIR"
    sudo chmod -R 755 "$NEW_DIR"

    # Start services in new environment
    sudo systemctl start "bodyscript-api-$NEW_ENV"

    # Wait for service to be ready
    sleep 30

    # Health check on new environment
    local new_port
    if [ "$NEW_ENV" = "blue" ]; then
        new_port=8001
    else
        new_port=8002
    fi

    if curl -f "http://localhost:$new_port/health" > /dev/null 2>&1; then
        success "New environment ($NEW_ENV) is healthy"
    else
        error "New environment ($NEW_ENV) failed health check"
    fi

    # Switch traffic to new environment
    sudo rm -f /var/www/bodyscript-current
    sudo ln -s "$NEW_DIR" /var/www/bodyscript-current
    sudo nginx -s reload

    # Stop old environment services
    sudo systemctl stop "bodyscript-api-$OLD_ENV" || true

    success "Blue-green deployment completed. Active: $NEW_ENV"
}

# Comprehensive health checks
comprehensive_health_check() {
    log "Running comprehensive health checks..."

    # Basic connectivity
    if curl -f "$PRODUCTION_URL" > /dev/null 2>&1; then
        success "Frontend is responding"
    else
        error "Frontend health check failed"
    fi

    # API health
    if curl -f "$PRODUCTION_API_URL/health" > /dev/null 2>&1; then
        success "API is responding"
    else
        error "API health check failed"
    fi

    # Database connectivity
    if curl -f "$PRODUCTION_API_URL/health/database" > /dev/null 2>&1; then
        success "Database connectivity verified"
    else
        error "Database health check failed"
    fi

    # MediaPipe processing
    if curl -f "$PRODUCTION_API_URL/health/pose" > /dev/null 2>&1; then
        success "Pose processing is healthy"
    else
        error "Pose processing health check failed"
    fi

    # Performance check
    response_time=$(curl -o /dev/null -s -w '%{time_total}' "$PRODUCTION_URL")
    if (( $(echo "$response_time < 2.0" | bc -l) )); then
        success "Performance check passed: ${response_time}s"
    else
        warning "Performance check: slow response time ${response_time}s"
    fi

    success "All health checks passed"
}

# Post-deployment monitoring setup
setup_monitoring() {
    log "Setting up post-deployment monitoring..."

    # Create monitoring script
    cat > /tmp/deployment-monitor.sh << 'EOF'
#!/bin/bash
# Monitor deployment for the first hour

for i in {1..12}; do
    sleep 300  # 5 minutes

    if ! curl -f https://bodyscript.com/health > /dev/null 2>&1; then
        echo "Health check failed at $(date)" >> /var/log/bodyscript/post-deployment.log
        # Send alert
        curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"🚨 Production health check failed after deployment"}' \
            "$SLACK_WEBHOOK_URL" || true
    fi
done
EOF

    sudo mv /tmp/deployment-monitor.sh /usr/local/bin/
    sudo chmod +x /usr/local/bin/deployment-monitor.sh

    # Start monitoring in background
    nohup /usr/local/bin/deployment-monitor.sh > /dev/null 2>&1 &

    success "Post-deployment monitoring configured"
}

# Cleanup and finalization
finalize_deployment() {
    log "Finalizing deployment..."

    # Clean up temporary files
    rm -f .env build-info.txt

    # Update deployment record
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),$(git rev-parse HEAD),production,success" >> /var/log/bodyscript/deployments.csv

    # Send success notification
    send_slack_notification "✅ Production deployment completed successfully!"

    success "Deployment finalized"
}

# Main production deployment flow
main() {
    log "Starting production deployment..."
    send_slack_notification "🚀 Starting production deployment..."

    pre_deployment_checks
    create_backup
    install_dependencies
    run_comprehensive_tests
    build_production
    deploy_blue_green
    comprehensive_health_check
    setup_monitoring
    finalize_deployment

    success "Production deployment completed successfully!"
    log "Production URL: $PRODUCTION_URL"
    log "API URL: $PRODUCTION_API_URL"
    log "Backup location: $BACKUP_DIR"
}

# Emergency rollback
emergency_rollback() {
    log "Performing emergency rollback..."
    send_slack_notification "⚠️ Emergency rollback initiated"

    # Switch to previous deployment
    if [ -d "/var/www/bodyscript-blue" ] && [ -d "/var/www/bodyscript-green" ]; then
        current_env=$(readlink /var/www/bodyscript-current | grep -o 'blue\|green')
        if [ "$current_env" = "blue" ]; then
            rollback_env="green"
        else
            rollback_env="blue"
        fi

        sudo rm -f /var/www/bodyscript-current
        sudo ln -s "/var/www/bodyscript-$rollback_env" /var/www/bodyscript-current
        sudo systemctl start "bodyscript-api-$rollback_env"
        sudo nginx -s reload

        success "Emergency rollback to $rollback_env completed"
        send_slack_notification "✅ Emergency rollback completed"
    else
        error "No previous deployment found for rollback"
    fi
}

# Script execution
case "${1:-}" in
    "--rollback")
        emergency_rollback
        ;;
    "--health-check")
        comprehensive_health_check
        ;;
    *)
        main
        ;;
esac