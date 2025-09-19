#!/bin/bash

# =============================================================================
# OmniDesk AI Backup Script
# =============================================================================

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)
COMPOSE_FILE="docker-compose.prod.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log_info "Starting backup at $(date)"

# Database backup
log_info "Creating database backup..."
DB_BACKUP_FILE="$BACKUP_DIR/omnidesk_db_backup_$DATE.sql"

# Get database connection details from environment
if docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$DB_BACKUP_FILE"; then
    gzip "$DB_BACKUP_FILE"
    log_success "Database backup created: ${DB_BACKUP_FILE}.gz"
else
    log_error "Database backup failed"
    exit 1
fi

# Application data backup
log_info "Creating application data backup..."
UPLOADS_BACKUP_FILE="$BACKUP_DIR/omnidesk_uploads_backup_$DATE.tar.gz"

if docker-compose -f "$COMPOSE_FILE" exec -T backend tar -czf - -C /app uploads/ > "$UPLOADS_BACKUP_FILE"; then
    log_success "Uploads backup created: $UPLOADS_BACKUP_FILE"
else
    log_warning "Uploads backup failed (this may be normal if no uploads exist)"
fi

# Vector database backup
log_info "Creating vector database backup..."
QDRANT_BACKUP_FILE="$BACKUP_DIR/omnidesk_qdrant_backup_$DATE.tar.gz"

if docker-compose -f "$COMPOSE_FILE" exec -T qdrant tar -czf - -C /qdrant storage/ > "$QDRANT_BACKUP_FILE"; then
    log_success "Vector database backup created: $QDRANT_BACKUP_FILE"
else
    log_warning "Vector database backup failed"
fi

# Configuration backup
log_info "Creating configuration backup..."
CONFIG_BACKUP_FILE="$BACKUP_DIR/omnidesk_config_backup_$DATE.tar.gz"

tar -czf "$CONFIG_BACKUP_FILE" \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env*' \
    nginx/ monitoring/ scripts/ docker-compose*.yml .env.example 2>/dev/null || true

log_success "Configuration backup created: $CONFIG_BACKUP_FILE"

# Clean old backups
log_info "Cleaning old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "omnidesk_*_backup_*.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "omnidesk_*_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Upload to S3 if configured
if [[ -n "$AWS_ACCESS_KEY_ID" ]] && [[ -n "$BACKUP_S3_BUCKET" ]]; then
    log_info "Uploading backups to S3..."
    
    # Install AWS CLI in container if not available
    if ! command -v aws &> /dev/null; then
        log_warning "AWS CLI not available, skipping S3 upload"
    else
        aws s3 cp "$BACKUP_DIR/" "s3://$BACKUP_S3_BUCKET/omnidesk-backups/$(date +%Y/%m/%d)/" \
            --recursive \
            --exclude "*" \
            --include "*backup_$DATE*" \
            && log_success "Backups uploaded to S3" \
            || log_warning "S3 upload failed"
    fi
fi

# Generate backup report
BACKUP_REPORT="$BACKUP_DIR/backup_report_$DATE.txt"
cat > "$BACKUP_REPORT" << EOF
OmniDesk AI Backup Report
========================
Date: $(date)
Backup ID: $DATE

Files Created:
- Database: ${DB_BACKUP_FILE}.gz ($(du -h "${DB_BACKUP_FILE}.gz" 2>/dev/null | cut -f1 || echo "N/A"))
- Uploads: $UPLOADS_BACKUP_FILE ($(du -h "$UPLOADS_BACKUP_FILE" 2>/dev/null | cut -f1 || echo "N/A"))
- Vector DB: $QDRANT_BACKUP_FILE ($(du -h "$QDRANT_BACKUP_FILE" 2>/dev/null | cut -f1 || echo "N/A"))
- Config: $CONFIG_BACKUP_FILE ($(du -h "$CONFIG_BACKUP_FILE" 2>/dev/null | cut -f1 || echo "N/A"))

Total Backup Size: $(du -sh "$BACKUP_DIR" | cut -f1)
Retention Policy: $RETENTION_DAYS days

Status: SUCCESS
EOF

log_success "Backup completed successfully at $(date)"
log_info "Backup report: $BACKUP_REPORT"

# Send notification if webhook is configured
if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ OmniDesk AI backup completed successfully at $(date)\"}" \
        "$SLACK_WEBHOOK_URL" &>/dev/null || true
fi

exit 0