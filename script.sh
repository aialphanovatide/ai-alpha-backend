#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status.

# # Set environment variables
export FLASK_APP=server.py
export FLASK_ENV=${FLASK_ENV:-development} # if FLASK_ENV not set in .env file, then this variable will be used.

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

# Check, create, and apply migration
check_create_and_apply_migrations

# Start the application
if [ "$FLASK_ENV" = "development" ]; then
    echo "Starting Flask development server..."
    python server.py --host=0.0.0.0 --port=9002
else
    echo "Starting Gunicorn production server..."
    PORT=${PORT:-9002}
    exec gunicorn --bind 0.0.0.0:$PORT --workers 3 --threads 2 --timeout 120 server:app
fi
