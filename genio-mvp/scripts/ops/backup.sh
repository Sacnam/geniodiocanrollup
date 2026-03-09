#!/bin/bash
# Genio Platform Backup Script
# Backs up PostgreSQL, Redis, and Qdrant data

set -e

BACKUP_DIR="/var/backups/genio"
S3_BUCKET="${GENIO_BACKUP_S3_BUCKET:-genio-backups}"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# PostgreSQL Backup
log "Backing up PostgreSQL..."
if [ -z "$DATABASE_URL" ]; then
    error "DATABASE_URL not set"
fi

# Extract connection details from URL
pg_dump "$DATABASE_URL" \
    --format=custom \
    --file="$BACKUP_DIR/$DATE/postgres.dump" \
    --verbose

log "PostgreSQL backup complete"

# Redis Backup
log "Backing up Redis..."
redis-cli BGSAVE

# Wait for BGSAVE to complete
while redis-cli INFO persistence | grep -q "rdb_bgsave_in_progress:1"; do
    sleep 1
done

# Copy Redis dump
if [ -f /data/redis/dump.rdb ]; then
    cp /data/redis/dump.rdb "$BACKUP_DIR/$DATE/redis.rdb"
elif [ -f /var/lib/redis/dump.rdb ]; then
    cp /var/lib/redis/dump.rdb "$BACKUP_DIR/$DATE/redis.rdb"
else
    warn "Redis dump.rdb not found in standard locations"
fi

log "Redis backup complete"

# Qdrant Backup
log "Backing up Qdrant..."
if curl -s http://localhost:6333 | grep -q "Qdrant"; then
    # Create Qdrant snapshot
    curl -X POST http://localhost:6333/collections/articles/snapshots \
        -H "Content-Type: application/json" \
        -d '{"name": "backup_'$DATE'"}'
    
    # Copy snapshot
    cp /qdrant/snapshots/articles/backup_$DATE "$BACKUP_DIR/$DATE/qdrant.snapshot" || \
        warn "Could not copy Qdrant snapshot"
else
    warn "Qdrant not accessible"
fi

log "Qdrant backup complete"

# Create manifest
cat > "$BACKUP_DIR/$DATE/manifest.json" <<EOF
{
    "timestamp": "$DATE",
    "version": "1.0",
    "components": {
        "postgresql": "postgres.dump",
        "redis": "redis.rdb",
        "qdrant": "qdrant.snapshot"
    },
    "checksums": {
        "postgres": "$(md5sum $BACKUP_DIR/$DATE/postgres.dump | cut -d' ' -f1)",
        "redis": "$(md5sum $BACKUP_DIR/$DATE/redis.rdb 2>/dev/null | cut -d' ' -f1 || echo 'N/A')"
    }
}
EOF

# Compress backup
log "Compressing backup..."
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"
rm -rf "$BACKUP_DIR/$DATE"

BACKUP_SIZE=$(du -h "$BACKUP_DIR/backup_$DATE.tar.gz" | cut -f1)
log "Backup created: backup_$DATE.tar.gz ($BACKUP_SIZE)"

# Upload to S3
if command -v aws &> /dev/null; then
    log "Uploading to S3..."
    aws s3 cp "$BACKUP_DIR/backup_$DATE.tar.gz" "s3://$S3_BUCKET/backups/" \
        --storage-class STANDARD_IA
    log "Upload complete"
else
    warn "AWS CLI not found, skipping S3 upload"
fi

# Cleanup old backups
log "Cleaning up old backups (>$RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Also cleanup S3
if command -v aws &> /dev/null; then
    aws s3 ls "s3://$S3_BUCKET/backups/" | \
        awk '{print $4}' | \
        while read file; do
            # Extract date from filename and check age
            file_date=$(echo $file | grep -oP '\d{8}')
            if [ -n "$file_date" ]; then
                file_epoch=$(date -d "$file_date" +%s 2>/dev/null || date -j -f "%Y%m%d" "$file_date" +%s)
                current_epoch=$(date +%s)
                age_days=$(( (current_epoch - file_epoch) / 86400 ))
                
                if [ $age_days -gt $RETENTION_DAYS ]; then
                    aws s3 rm "s3://$S3_BUCKET/backups/$file"
                fi
            fi
        done
fi

log "Backup complete: backup_$DATE.tar.gz"
