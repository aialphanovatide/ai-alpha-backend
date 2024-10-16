#!/bin/bash
set -e

# Function to check if the database is empty
is_db_empty() {
    local db_name="$1"
    local table_count=$(psql -U "$POSTGRES_USER" -d "$db_name" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    [ "$table_count" -eq 0 ]
}

# Wait for the database to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    echo "Waiting for database to be ready..."
    sleep 2
done

# Check if the database is empty
if is_db_empty "$POSTGRES_DB"; then
    echo "Database is empty. Restoring from backup..."
    if [ -f "$BACKUP_FILE" ]; then
        pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$BACKUP_FILE"
        echo "Backup restored successfully."
    else
        echo "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
else
    echo "Database is not empty. Skipping backup restore."
fi