#!/bin/bash

# BodyScript Rollback Script
# Emergency rollback procedures for staging and production environments

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_BASE_DIR="/backup/bodyscript"
LOG_FILE="/var/log/bodyscript/rollback.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${BLUE}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

success() {
    local message="[SUCCESS] $1"
    echo -e "${GREEN}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

warning() {
    local message="[WARNING] $1"
    echo -e "${YELLOW}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

error() {
    local message="[ERROR] $1"
    echo -e "${RED}$message${NC}"
    echo "$message" >> "$LOG_FILE"
    exit 1
}

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS] <environment>

ENVIRONMENTS:
  staging     Rollback staging environment
  production  Rollback production environment

OPTIONS:
  -v, --version VERSION      Rollback to specific version/backup
  -l, --list                 List available backups
  -f, --force                Force rollback without confirmation
  -h, --help                 Show this help message

EXAMPLES:
  $0 staging                           # Rollback staging to latest backup
  $0 production --version 20240924     # Rollback production to specific backup
  $0 --list staging                    # List staging backups
  $0 production --force                # Force production rollback
EOF
}

# List available backups
list_backups() {
    local environment="$1"
    local backup_dir="$BACKUP_BASE_DIR/$environment"

    log "Available backups for $environment:"

    if [ ! -d "$backup_dir" ]; then
        warning "No backup directory found: $backup_dir"
        return 1
    fi

    echo -e "\nBackup ID\t\tDate\t\t\tSize\t\tType"
    echo "--------------------------------------------------------------------"

    for backup in $(ls -1t "$backup_dir" 2>/dev/null || true); do
        if [ -d "$backup_dir/$backup" ]; then
            local backup_date=$(stat -c %y "$backup_dir/$backup" 2>/dev/null | cut -d' ' -f1)
            local backup_size=$(du -sh "$backup_dir/$backup" 2>/dev/null | cut -f1)
            local backup_type="Unknown"

            # Determine backup type
            if [ -f "$backup_dir/$backup/deployment.tar.gz" ]; then
                backup_type="Full"
            elif [ -f "$backup_dir/$backup/database.sql" ]; then
                backup_type="Database"
            elif [ -d "$backup_dir/$backup/frontend" ]; then
                backup_type="Frontend"
            fi

            echo -e "$backup\t$backup_date\t\t$backup_size\t\t$backup_type"
        fi
    done

    echo ""
}

# Get latest backup
get_latest_backup() {
    local environment="$1"
    local backup_dir="$BACKUP_BASE_DIR/$environment"

    if [ ! -d "$backup_dir" ]; then
        error "No backup directory found: $backup_dir"
    fi

    local latest_backup=$(ls -1t "$backup_dir" | head -1 2>/dev/null || true)

    if [ -z "$latest_backup" ]; then
        error "No backups found in $backup_dir"
    fi

    echo "$latest_backup"
}

# Validate backup
validate_backup() {
    local environment="$1"
    local backup_id="$2"
    local backup_dir="$BACKUP_BASE_DIR/$environment/$backup_id"

    log "Validating backup: $backup_id"

    if [ ! -d "$backup_dir" ]; then
        error "Backup not found: $backup_dir"
    fi

    # Check for required backup components
    local has_deployment=false
    local has_database=false
    local has_config=false

    if [ -f "$backup_dir/deployment.tar.gz" ]; then
        has_deployment=true
        log "✓ Deployment backup found"
    fi

    if [ -f "$backup_dir/database.sql" ]; then
        has_database=true
        log "✓ Database backup found"
    fi

    if [ -f "$backup_dir/nginx.conf" ] || [ -f "$backup_dir/config" ]; then
        has_config=true
        log "✓ Configuration backup found"
    fi

    if [ "$has_deployment" = false ] && [ "$has_database" = false ]; then
        error "Invalid backup: No deployment or database backup found"
    fi

    success "Backup validation completed"
}

# Create pre-rollback snapshot
create_pre_rollback_snapshot() {
    local environment="$1"
    local snapshot_dir="$BACKUP_BASE_DIR/$environment/pre-rollback-$(date +%Y%m%d_%H%M%S)"

    log "Creating pre-rollback snapshot..."

    mkdir -p "$snapshot_dir"

    # Backup current deployment if it exists
    if [ "$environment" = "production" ]; then
        local deployment_dir="/var/www/bodyscript"
    else
        local deployment_dir="/var/www/bodyscript-staging"
    fi

    if [ -d "$deployment_dir" ]; then
        tar -czf "$snapshot_dir/current-deployment.tar.gz" -C "$deployment_dir" .
        success "Current deployment snapshot created"
    fi

    # Backup current database
    if command -v pg_dump &> /dev/null; then
        local db_name
        if [ "$environment" = "production" ]; then
            db_name="bodyscript"
        else
            db_name="bodyscript_staging"
        fi

        sudo -u postgres pg_dump "$db_name" > "$snapshot_dir/current-database.sql" || true
        success "Current database snapshot created"
    fi

    echo "$snapshot_dir" > "/tmp/bodyscript-rollback-snapshot"
    success "Pre-rollback snapshot created: $snapshot_dir"
}

# Rollback application deployment
rollback_deployment() {
    local environment="$1"
    local backup_id="$2"
    local backup_dir="$BACKUP_BASE_DIR/$environment/$backup_id"

    log "Rolling back application deployment..."

    # Determine deployment directory
    if [ "$environment" = "production" ]; then
        local deployment_dir="/var/www/bodyscript"
        local service_name="bodyscript-api"
    else
        local deployment_dir="/var/www/bodyscript-staging"
        local service_name="bodyscript-api-staging"
    fi

    # Stop services
    log "Stopping application services..."
    sudo systemctl stop "$service_name" || warning "Failed to stop $service_name"

    # Backup current deployment
    if [ -d "$deployment_dir" ]; then
        sudo mv "$deployment_dir" "${deployment_dir}.rollback-backup-$(date +%Y%m%d_%H%M%S)"
    fi

    # Restore from backup
    if [ -f "$backup_dir/deployment.tar.gz" ]; then
        sudo mkdir -p "$deployment_dir"
        sudo tar -xzf "$backup_dir/deployment.tar.gz" -C "$deployment_dir"
        success "Deployment restored from backup"
    elif [ -d "$backup_dir/frontend" ] && [ -d "$backup_dir/backend" ]; then
        sudo mkdir -p "$deployment_dir"
        sudo cp -r "$backup_dir/frontend"/* "$deployment_dir/"
        sudo cp -r "$backup_dir/backend" "$deployment_dir/"
        success "Deployment restored from directory backup"
    else
        error "No deployment backup found in $backup_dir"
    fi

    # Set proper permissions
    sudo chown -R www-data:www-data "$deployment_dir"
    sudo chmod -R 755 "$deployment_dir"

    # Restore configuration
    if [ -f "$backup_dir/nginx.conf" ]; then
        sudo cp "$backup_dir/nginx.conf" "/etc/nginx/sites-available/bodyscript"
        log "Nginx configuration restored"
    fi

    if [ -f "$backup_dir/systemd.service" ]; then
        sudo cp "$backup_dir/systemd.service" "/etc/systemd/system/$service_name.service"
        sudo systemctl daemon-reload
        log "Systemd service configuration restored"
    fi

    # Start services
    log "Starting application services..."
    sudo systemctl start "$service_name"
    sudo systemctl reload nginx

    success "Application deployment rollback completed"
}

# Rollback database
rollback_database() {
    local environment="$1"
    local backup_id="$2"
    local backup_dir="$BACKUP_BASE_DIR/$environment/$backup_id"

    if [ ! -f "$backup_dir/database.sql" ]; then
        warning "No database backup found, skipping database rollback"
        return 0
    fi

    log "Rolling back database..."

    # Determine database name
    if [ "$environment" = "production" ]; then
        local db_name="bodyscript"
    else
        local db_name="bodyscript_staging"
    fi

    # Create current database backup before rollback
    local current_backup="$BACKUP_BASE_DIR/$environment/pre-rollback-db-$(date +%Y%m%d_%H%M%S).sql"
    sudo -u postgres pg_dump "$db_name" > "$current_backup" || warning "Failed to backup current database"

    # Drop and recreate database
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${db_name};"
    sudo -u postgres psql -c "CREATE DATABASE ${db_name};"

    # Restore database from backup
    sudo -u postgres psql "$db_name" < "$backup_dir/database.sql"

    success "Database rollback completed"
}

# Health check after rollback
post_rollback_health_check() {
    local environment="$1"

    log "Running post-rollback health checks..."

    # Determine URLs
    if [ "$environment" = "production" ]; then
        local frontend_url="https://bodyscript.com"
        local api_url="https://api.bodyscript.com"
    else
        local frontend_url="https://bodyscript-staging.example.com"
        local api_url="https://api-staging.bodyscript.example.com"
    fi

    # Wait for services to start
    sleep 30

    # Check frontend
    if curl -f "$frontend_url" > /dev/null 2>&1; then
        success "Frontend health check passed"
    else
        error "Frontend health check failed"
    fi

    # Check API
    if curl -f "$api_url/health" > /dev/null 2>&1; then
        success "API health check passed"
    else
        error "API health check failed"
    fi

    # Check database connectivity
    if curl -f "$api_url/health/database" > /dev/null 2>&1; then
        success "Database connectivity check passed"
    else
        warning "Database connectivity check failed"
    fi

    success "Post-rollback health checks completed"
}

# Send notifications
send_notifications() {
    local environment="$1"
    local backup_id="$2"
    local success="$3"

    local webhook_url="${SLACK_WEBHOOK_URL:-}"

    if [ -n "$webhook_url" ]; then
        local status_emoji
        local color
        local message

        if [ "$success" = "true" ]; then
            status_emoji="✅"
            color="good"
            message="Rollback to backup $backup_id completed successfully"
        else
            status_emoji="❌"
            color="danger"
            message="Rollback to backup $backup_id failed"
        fi

        local payload=$(cat << EOF
{
    "text": "$status_emoji $environment rollback",
    "attachments": [
        {
            "color": "$color",
            "title": "BodyScript Rollback - $environment",
            "fields": [
                {
                    "title": "Status",
                    "value": "$message",
                    "short": false
                },
                {
                    "title": "Backup ID",
                    "value": "$backup_id",
                    "short": true
                },
                {
                    "title": "Timestamp",
                    "value": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
                    "short": true
                }
            ]
        }
    ]
}
EOF
        )

        curl -X POST -H 'Content-type: application/json' \
             --data "$payload" "$webhook_url" || true
    fi
}

# Main rollback function
perform_rollback() {
    local environment="$1"
    local backup_id="$2"
    local force="$3"

    log "Starting rollback for $environment environment"
    log "Backup ID: $backup_id"

    # Confirmation
    if [ "$force" != "true" ]; then
        echo -e "\n${YELLOW}WARNING: This will rollback $environment to backup $backup_id${NC}"
        echo "This action cannot be undone automatically."
        read -p "Are you sure you want to continue? (yes/no): " -r

        if [ "$REPLY" != "yes" ]; then
            log "Rollback cancelled by user"
            exit 0
        fi
    fi

    # Validate backup
    validate_backup "$environment" "$backup_id"

    # Create pre-rollback snapshot
    create_pre_rollback_snapshot "$environment"

    local rollback_success=false

    # Perform rollback
    if rollback_deployment "$environment" "$backup_id" && \
       rollback_database "$environment" "$backup_id" && \
       post_rollback_health_check "$environment"; then
        rollback_success=true
        success "Rollback completed successfully!"
    else
        rollback_success=false
        error "Rollback failed!"
    fi

    # Send notifications
    send_notifications "$environment" "$backup_id" "$rollback_success"

    # Log final status
    if [ "$rollback_success" = "true" ]; then
        log "Rollback completed successfully for $environment environment"

        # Cleanup old snapshots (keep last 5)
        find "$BACKUP_BASE_DIR/$environment" -name "pre-rollback-*" -type d | sort -r | tail -n +6 | xargs rm -rf || true
    else
        log "Rollback failed for $environment environment"
        exit 1
    fi
}

# Parse command line arguments
ENVIRONMENT=""
VERSION=""
LIST_BACKUPS=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -l|--list)
            LIST_BACKUPS=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        staging|production)
            ENVIRONMENT="$1"
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate arguments
if [ -z "$ENVIRONMENT" ]; then
    error "Environment is required. Use 'staging' or 'production'"
fi

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    error "Invalid environment: $ENVIRONMENT. Use 'staging' or 'production'"
fi

# Handle list command
if [ "$LIST_BACKUPS" = true ]; then
    list_backups "$ENVIRONMENT"
    exit 0
fi

# Determine backup version
if [ -z "$VERSION" ]; then
    VERSION=$(get_latest_backup "$ENVIRONMENT")
    log "Using latest backup: $VERSION"
else
    log "Using specified backup: $VERSION"
fi

# Perform rollback
perform_rollback "$ENVIRONMENT" "$VERSION" "$FORCE"