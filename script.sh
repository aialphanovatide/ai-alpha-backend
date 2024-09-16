#!/bin/bash

# Set environment variables
export FLASK_APP=server.py
export FLASK_ENV=development  # Change to 'production' for prod environment

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

# Print DATABASE_URL for debugging
# echo "DATABASE_URL: $DATABASE_URL"

# Start the Flask application
python server.py --host=0.0.0.0 --port=9000