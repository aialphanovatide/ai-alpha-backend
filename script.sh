#!/bin/bash

# Set environment variables
export FLASK_APP=server.py
export FLASK_ENV=${FLASK_ENV:-development}  # Use production as default if not set

# Load environment variables from .env file
if [ "$FLASK_ENV" = "development" ]; then
    ENV_FILE=.env.dev
else
    ENV_FILE=.env.prod
fi

if [ -f "$ENV_FILE" ]; then
    set -a  # automatically export all variables
    . "$ENV_FILE"
    set +a
else
    echo "Error: $ENV_FILE not found."
    exit 1
fi

# Function to check and apply Alembic migrations
check_and_apply_migrations() {
    echo "Checking for pending database migrations..."
    
    # Get the current revision and the head revision
    current_rev=$(alembic current 2>/dev/null | grep "^[a-f0-9]\+" | cut -d' ' -f1)
    head_rev=$(alembic heads 2>/dev/null | grep "^[a-f0-9]\+" | cut -d' ' -f1)

    if [ "$current_rev" != "$head_rev" ]; then
        echo "Pending migrations found. Applying migrations..."
        alembic upgrade head
        if [ $? -eq 0 ]; then
            echo "Migrations applied successfully."
        else
            echo "Error applying migrations. Exiting."
            exit 1
        fi
    else
        echo "Database is up to date. No migrations needed."
    fi
}

# Check and apply migrations
check_and_apply_migrations

# Start the application
if [ "$FLASK_ENV" = "development" ]; then
    echo "Starting Flask development server..."
    python server.py --host=0.0.0.0 --port=9000
else
    echo "Starting Gunicorn production server..."
    gunicorn --bind 0.0.0.0:9000 --workers 4 --threads 2 server:app
fi