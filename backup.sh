#!/bin/bash
# Backup script for Pantry Inventory database and Redis

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Starting backup at $(date)"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker-compose exec -T db pg_dump -U pantry pantry_db | gzip > "$BACKUP_DIR/pantry_db_$TIMESTAMP.sql.gz"
echo "✓ PostgreSQL backup: $BACKUP_DIR/pantry_db_$TIMESTAMP.sql.gz"

# Backup Redis
echo "Backing up Redis..."
docker-compose exec -T redis redis-cli BGSAVE
sleep 2
docker cp pantry-redis:/data/dump.rdb "$BACKUP_DIR/redis_$TIMESTAMP.rdb"
echo "✓ Redis backup: $BACKUP_DIR/redis_$TIMESTAMP.rdb"

# Clean up old backups (keep last 30 days)
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -type f -mtime +30 -delete
echo "✓ Old backups cleaned"

# Show backup summary
echo ""
echo "Backup Summary:"
ls -lh "$BACKUP_DIR" | tail -5

echo "Backup complete at $(date)"
