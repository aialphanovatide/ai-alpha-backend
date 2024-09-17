#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status.

# Set environment variables
export FLASK_APP=server.py
export FLASK_ENV=${FLASK_ENV:-development}

# Load environment variables from .env file
if [ "$FLASK_ENV" = "development" ]; then
    ENV_FILE=.env.dev
else
    ENV_FILE=.env.prod
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