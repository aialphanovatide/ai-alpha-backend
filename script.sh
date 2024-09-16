#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status.

# # Debug: Print current directory and list files
# echo "Current directory: $(pwd)"
# echo "Files in current directory:"
# ls -la

# Set environment variables
export FLASK_APP=server.py
export FLASK_ENV=${FLASK_ENV:-development}

# Load environment variables from .env file
if [ "$FLASK_ENV" = "development" ]; then
    ENV_FILE=/app/.env.dev
else
    ENV_FILE=/app/.env.prod
fi

if [ -f "$ENV_FILE" ]; then
    echo "Loading environment from $ENV_FILE"
    set -a
    . "$ENV_FILE"
    set +a
else
    echo "Error: $ENV_FILE not found."
    exit 1
fi

# Check if required environment variables are set
required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "DATABASE_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set."
        exit 1
    fi
done

# Function to check database connection
check_db_connection() {
    echo "Checking database connection..."
    max_retries=5
    count=0
    while [ $count -lt $max_retries ]; do
        if PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U $POSTGRES_USER -d $POSTGRES_DB -c '\q' 2>/dev/null; then
            echo "Successfully connected to the database."
            return 0
        fi
        echo "Failed to connect to the database. Retrying in 5 seconds..."
        sleep 5
        count=$((count + 1))
    done
    echo "Error: Could not connect to the database after $max_retries attempts."
    return 1
}

# Check database connection
check_db_connection || exit 1

# Function to check, create, and apply Alembic migrations
check_create_and_apply_migrations() {
    echo "Checking for pending database migrations..."
    
    # Get the current revision and the head revision
    current_rev=$(alembic current 2>/dev/null | grep "^[a-f0-9]\+" | cut -d' ' -f1)
    head_rev=$(alembic heads 2>/dev/null | grep "^[a-f0-9]\+" | cut -d' ' -f1)

    if [ -z "$current_rev" ] && [ -z "$head_rev" ]; then
        echo "No migrations found. Creating initial migration..."
        alembic revision --autogenerate -m "Initial migration"
        if [ $? -eq 0 ]; then
            echo "Initial migration created successfully."
            alembic upgrade head
        else
            echo "Error creating initial migration. Exiting."
            exit 1
        fi
    elif [ "$current_rev" != "$head_rev" ]; then
        echo "Pending migrations found. Applying migrations..."
        alembic upgrade head
    else
        echo "Database schema is up to date."
    fi
}

# Check, create, and apply migrations
check_create_and_apply_migrations

# Start the application
if [ "$FLASK_ENV" = "development" ]; then
    echo "Starting Flask development server..."
    python server.py --host=0.0.0.0 --port=9000
else
    echo "Starting Gunicorn production server..."
    gunicorn --bind 0.0.0.0:9000 --workers 4 --threads 2 server:app
fi