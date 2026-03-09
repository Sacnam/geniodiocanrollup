#!/bin/bash
# Genio Platform Restore Script
# Restores PostgreSQL, Redis, and Qdrant from backup

set -e

BACKUP_FILE="$1"
TEMP_DIR="/tmp/genio_restore"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo "Example: $0 /var/backups/genio/backup_20260217_120000.tar.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +%Y-%m-%d\ %H:%M:%S)]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Confirmation
warn "This will OVERWRITE existing data!"
read -p "Are you sure you want to continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log "Restore cancelled"
    exit 0
fi

# Extract backup
log "Extracting backup..."
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

BACKUP_DIR=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)
log "Backup directory: $BACKUP_DIR"

# Verify manifest
if [ -f "$BACKUP_DIR/manifest.json" ]; then
    log "Manifest found:"
    cat "$BACKUP_DIR/manifest.json"
else
    warn "Manifest not found"
fi

# Stop services
log "Stopping services..."
docker-compose stop api worker beat || true

# Restore PostgreSQL
if [ -f "$BACKUP_DIR/postgres.dump" ]; then
    log "Restoring PostgreSQL..."
    
    if [ -z "$DATABASE_URL" ]; then
        error "DATABASE_URL not set"
    fi
    
    # Drop and recreate database
    psql "$DATABASE_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || true
    
    # Restore
    pg_restore \
        --clean \
        --if-exists \
        --verbose \
        --dbname="$DATABASE_URL" \
        "$BACKUP_DIR/postgres.dump"
    
    log "PostgreSQL restore complete"
else
    warn "PostgreSQL dump not found"
fi

# Restore Redis
if [ -f "$BACKUP_DIR/redis.rdb" ]; then
    log "Restoring Redis..."
    
    # Stop Redis container
    docker-compose stop redis || true
    
    # Copy dump
    if [ -d /data/redis ]; then
        cp "$BACKUP_DIR/redis.rdb" /data/redis/dump.rdb
    elif [ -d /var/lib/redis ]; then
        cp "$BACKUP_DIR/redis.rdb" /var/lib/redis/dump.rdb
    else
        warn "Redis data directory not found"
    fi
    
    # Start Redis
    docker-compose start redis || true
    
    log "Redis restore complete"
else
    warn "Redis dump not found"
fi

# Restore Qdrant
if [ -f "$BACKUP_DIR/qdrant.snapshot" ]; then
    log "Restoring Qdrant..."
    
    # Upload snapshot and restore via API
    curl -X POST http://localhost:6333/collections/articles/snapshots/upload \
        -H "Content-Type: multipart/form-data" \
        -F "snapshot=@$BACKUP_DIR/qdrant.snapshot"
    
    log "Qdrant restore complete"
else
    warn "Qdrant snapshot not found"
fi

# Start services
log "Starting services..."
docker-compose start api worker beat || true

# Cleanup
rm -rf "$TEMP_DIR"

log "Restore complete!"
log "Verify the system with: docker-compose ps"
