#!/bin/bash

# Start script for SkillGraph API

# Function to check if a service is ready
check_service() {
    local service_name=$1
    local service_url=$2
    local max_attempts=$3
    local wait_time=$4

    echo "Waiting for $service_name to be ready..."

    for ((i=1; i<=max_attempts; i++)); do
        if curl -f "$service_url/health" > /dev/null 2>&1; then
            echo "$service_name is ready!"
            return 0
        else
            echo "Attempt $i/$max_attempts: $service_name not ready yet..."
            sleep $wait_time
        fi
    done

    echo "ERROR: $service_name failed to start after $max_attempts attempts"
    return 1
}

# Main startup sequence
echo "Starting SkillGraph API..."

# Wait for dependencies
check_service "PostgreSQL" "http://postgres:5432" 10 5
check_service "Redis" "http://redis:6379" 10 5

# Run migrations if any
echo "Running database migrations..."
# Add migration commands here

# Start the API server
echo "Starting API server..."
exec uvicorn skillgraph.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers ${WORKERS:-1} \
    --log-level ${LOG_LEVEL:-info}
    --access-log \
    --reload ${RELOAD:-false}
