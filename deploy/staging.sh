#!/bin/bash

# BodyScript Staging Deployment Script
# This script handles deployment to staging environment with safety checks

set -euo pipefail

# Configuration
STAGING_BRANCH="develop"
STAGING_URL="https://bodyscript-staging.example.com"
STAGING_API_URL="https://api-staging.bodyscript.example.com"
BACKUP_DIR="/tmp/bodyscript-backup-$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."

    # Check if we're on the right branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$STAGING_BRANCH" ]; then
        warning "Not on staging branch ($STAGING_BRANCH). Current: $current_branch"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Deployment cancelled"
        fi
    fi

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        error "Uncommitted changes detected. Please commit or stash changes first."
    fi

    # Check if staging environment variables exist
    if [ ! -f ".env.staging" ]; then
        error "Staging environment file (.env.staging) not found"
    fi

    # Check Node.js and Python versions
    node_version=$(node --version)
    python_version=$(python --version 2>&1)
    log "Node.js version: $node_version"
    log "Python version: $python_version"

    success "Pre-deployment checks passed"
}

# Create backup
create_backup() {
    log "Creating backup..."
    mkdir -p "$BACKUP_DIR"

    # Backup current deployment if it exists
    if [ -d "/var/www/bodyscript-staging" ]; then
        cp -r /var/www/bodyscript-staging "$BACKUP_DIR/previous-deployment"
        success "Backup created at $BACKUP_DIR"
    else
        log "No previous deployment found to backup"
    fi
}

# Install dependencies
install_dependencies() {
    log "Installing Node.js dependencies..."
    npm ci --production=false

    log "Installing Python dependencies..."
    pip install -r backend/requirements.txt

    success "Dependencies installed"
}

# Run tests
run_tests() {
    log "Running test suite..."

    # Frontend tests
    npm run test:unit
    npm run lint

    # Backend tests
    cd backend && python -m pytest tests/ -v
    cd ..

    success "All tests passed"
}

# Build application
build_application() {
    log "Building application..."

    # Set staging environment
    export NODE_ENV=staging
    cp .env.staging .env

    # Build frontend
    npm run build

    # Build Python package
    cd backend && python setup.py build
    cd ..

    success "Application built successfully"
}

# Deploy to staging server
deploy_to_server() {
    log "Deploying to staging server..."

    # Copy built files to staging directory
    sudo mkdir -p /var/www/bodyscript-staging
    sudo cp -r frontend/dist/* /var/www/bodyscript-staging/
    sudo cp -r backend /var/www/bodyscript-staging/
    sudo cp .env.staging /var/www/bodyscript-staging/.env

    # Set proper permissions
    sudo chown -R www-data:www-data /var/www/bodyscript-staging
    sudo chmod -R 755 /var/www/bodyscript-staging

    # Restart services
    sudo systemctl restart nginx
    sudo systemctl restart bodyscript-api

    success "Deployment completed"
}

# Health check
health_check() {
    log "Running health checks..."

    # Check frontend
    if curl -f "$STAGING_URL" > /dev/null 2>&1; then
        success "Frontend is responding"
    else
        error "Frontend health check failed"
    fi

    # Check API
    if curl -f "$STAGING_API_URL/health" > /dev/null 2>&1; then
        success "API is responding"
    else
        error "API health check failed"
    fi

    # Check pose processing endpoint
    if curl -f "$STAGING_API_URL/api/health/pose" > /dev/null 2>&1; then
        success "Pose processing endpoint is healthy"
    else
        warning "Pose processing endpoint may have issues"
    fi
}

# Post-deployment cleanup
cleanup() {
    log "Cleaning up temporary files..."
    rm -f .env
    success "Cleanup completed"
}

# Main deployment flow
main() {
    log "Starting staging deployment..."

    pre_deployment_checks
    create_backup
    install_dependencies
    run_tests
    build_application
    deploy_to_server
    health_check
    cleanup

    success "Staging deployment completed successfully!"
    log "Staging URL: $STAGING_URL"
    log "API URL: $STAGING_API_URL"
    log "Backup location: $BACKUP_DIR"
}

# Rollback function
rollback() {
    log "Rolling back to previous deployment..."

    if [ -d "$BACKUP_DIR/previous-deployment" ]; then
        sudo cp -r "$BACKUP_DIR/previous-deployment"/* /var/www/bodyscript-staging/
        sudo systemctl restart nginx
        sudo systemctl restart bodyscript-api
        success "Rollback completed"
    else
        error "No backup found for rollback"
    fi
}

# Script execution
if [ "${1:-}" = "--rollback" ]; then
    rollback
else
    main
fi