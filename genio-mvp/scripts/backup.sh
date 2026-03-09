#!/bin/bash
#
# Genio Knowledge OS - Backup Script
# Creates encrypted backups of all data stores
#

set -e

# Configuration
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="genio_backup_${DATE}"
RETENTION_DAYS=30
S3_BUCKET="${BACKUP_S3_BUCKET:-genio-backups}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +%Y-%m-%d\ %H:%M:%S)]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Create backup directory
mkdir -p ${BACKUP_DIR}

cd ${BACKUP_DIR}

log "Starting backup: ${BACKUP_NAME}"

# 1. PostgreSQL Backup
log "Backing up PostgreSQL..."
docker-compose exec -T postgres pg_dumpall -c -U genio > ${BACKUP_NAME}_postgres.sql

if [ -n "$ENCRYPTION_KEY" ]; then
    gpg --symmetric --cipher-algo AES256 --passphrase "$ENCRYPTION_KEY" \
        --batch --yes -o ${BACKUP_NAME}_postgres.sql.gpg ${BACKUP_NAME}_postgres.sql
    rm ${BACKUP_NAME}_postgres.sql
    SQL_BACKUP="${BACKUP_NAME}_postgres.sql.gpg"
else
    SQL_BACKUP="${BACKUP_NAME}_postgres.sql"
fi

# 2. Redis Backup
log "Backing up Redis..."
docker-compose exec -T redis redis-cli BGSAVE
sleep 5  # Wait for BGSAVE to complete
docker cp $(docker-compose ps -q redis):/data/dump.rdb ${BACKUP_NAME}_redis.rdb

# 3. Elasticsearch Backup
log "Backing up Elasticsearch..."
curl -X PUT "localhost:9200/_snapshot/backup_repo/${BACKUP_NAME}?wait_for_completion=true" \
    -H 'Content-Type: application/json' \
    -d '{
        "indices": "genio_*",
        "ignore_unavailable": true,
        "include_global_state": false
    }'

# 4. Qdrant Backup
log "Backing up Qdrant..."
docker-compose exec -T qdrant tar czf - /qdrant/storage > ${BACKUP_NAME}_qdrant.tar.gz

# 5. Create manifest
log "Creating backup manifest..."
cat > ${BACKUP_NAME}_manifest.json <<EOF
{
    "backup_name": "${BACKUP_NAME}",
    "created_at": "$(date -Iseconds)",
    "version": "$(git -C /app rev-parse --short HEAD 2>/dev/null || echo 'unknown')",
    "files": [
        "${SQL_BACKUP}",
        "${BACKUP_NAME}_redis.rdb",
        "${BACKUP_NAME}_qdrant.tar.gz"
    ],
    "encrypted": $([ -n "$ENCRYPTION_KEY" ] && echo "true" || echo "false")
}
EOF

# 6. Upload to S3
if [ -n "$S3_BUCKET" ]; then
    log "Uploading to S3..."
    aws s3 sync . s3://${S3_BUCKET}/backups/${BACKUP_NAME}/ \
        --exclude "*" \
        --include "${BACKUP_NAME}*"
    
    log "Backup uploaded to: s3://${S3_BUCKET}/backups/${BACKUP_NAME}/"
fi

# 7. Cleanup old backups
log "Cleaning up old backups (>${RETENTION_DAYS} days)..."
find ${BACKUP_DIR} -name "genio_backup_*" -mtime +${RETENTION_DAYS} -delete

# 8. Cleanup old S3 backups
if [ -n "$S3_BUCKET" ]; then
    aws s3 ls s3://${S3_BUCKET}/backups/ | \
        awk '{print $2}' | \
        while read backup; do
            date_str=$(echo $backup | grep -oP '\d{8}')
            if [ -n "$date_str" ]; then
                backup_date=$(date -d "$date_str" +%s 2>/dev/null || date -j -f "%Y%m%d" "$date_str" +%s)
                current_date=$(date +%s)
                age_days=$(( (current_date - backup_date) / 86400 ))
                if [ $age_days -gt $RETENTION_DAYS ]; then
                    aws s3 rm s3://${S3_BUCKET}/backups/${backup} --recursive
                    log "Deleted old backup: $backup"
                fi
            fi
        done
fi

log "Backup complete: ${BACKUP_NAME}"
log "Size: $(du -sh ${BACKUP_DIR}/${BACKUP_NAME}* | tail -1 | cut -f1)"

# Send notification
if [ -n "$SLACK_WEBHOOK" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Backup completed: ${BACKUP_NAME}\"}" \
        $SLACK_WEBHOOK
fi
