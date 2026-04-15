#!/usr/bin/env bash
set -euo pipefail

REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
NEO4J_HOST="${NEO4J_HOST:-neo4j}"
NEO4J_PORT="${NEO4J_PORT:-7687}"

MAX_RETRIES="${MAX_RETRIES:-30}"
RETRY_INTERVAL="${RETRY_INTERVAL:-2}"

# -------------------------------------------------------------------
# Wait for Redis
# -------------------------------------------------------------------
echo "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
retries=0
until nc -z "${REDIS_HOST}" "${REDIS_PORT}" 2>/dev/null; do
    retries=$((retries + 1))
    if [ "${retries}" -ge "${MAX_RETRIES}" ]; then
        echo "ERROR: Redis not available after ${MAX_RETRIES} attempts. Exiting."
        exit 1
    fi
    echo "  Redis not ready (attempt ${retries}/${MAX_RETRIES}). Retrying in ${RETRY_INTERVAL}s..."
    sleep "${RETRY_INTERVAL}"
done
echo "Redis is ready."

# -------------------------------------------------------------------
# Wait for Neo4j
# -------------------------------------------------------------------
echo "Waiting for Neo4j at ${NEO4J_HOST}:${NEO4J_PORT}..."
retries=0
until nc -z "${NEO4J_HOST}" "${NEO4J_PORT}" 2>/dev/null; do
    retries=$((retries + 1))
    if [ "${retries}" -ge "${MAX_RETRIES}" ]; then
        echo "ERROR: Neo4j not available after ${MAX_RETRIES} attempts. Exiting."
        exit 1
    fi
    echo "  Neo4j not ready (attempt ${retries}/${MAX_RETRIES}). Retrying in ${RETRY_INTERVAL}s..."
    sleep "${RETRY_INTERVAL}"
done
echo "Neo4j is ready."

# -------------------------------------------------------------------
# Run database migrations
# -------------------------------------------------------------------
echo "Running graph database migrations..."
python -m app.migrations.init_graph
echo "Migrations complete."

# -------------------------------------------------------------------
# Start the application
# -------------------------------------------------------------------
echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
