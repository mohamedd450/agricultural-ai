#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------
# Wait for dependent services
# ------------------------------------------------------------------

wait_for_service() {
    local host="$1" port="$2" name="$3" retries="${4:-30}" wait_sec="${5:-2}"
    echo "Waiting for ${name} at ${host}:${port} ..."
    for i in $(seq 1 "$retries"); do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "${name} is ready."
            return 0
        fi
        echo "  attempt ${i}/${retries} – ${name} not ready, retrying in ${wait_sec}s ..."
        sleep "$wait_sec"
    done
    echo "WARNING: ${name} at ${host}:${port} did not become ready – continuing anyway."
    return 0
}

# Redis
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"

# Neo4j
NEO4J_HOST="${NEO4J_HOST:-localhost}"
NEO4J_PORT="${NEO4J_PORT:-7687}"
wait_for_service "$NEO4J_HOST" "$NEO4J_PORT" "Neo4j"

# ------------------------------------------------------------------
# Run migrations if requested
# ------------------------------------------------------------------

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "Running graph migrations ..."
    python -c "
import asyncio
from neo4j import AsyncGraphDatabase

from app.config import get_settings
from app.migrations.init_graph import init_graph
from app.migrations.seed_data import seed_data

async def migrate():
    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        await init_graph(driver)
        await seed_data(driver)
    finally:
        await driver.close()

asyncio.run(migrate())
"
    echo "Migrations complete."
fi

# ------------------------------------------------------------------
# Start the application
# ------------------------------------------------------------------

echo "Starting application ..."
exec "$@"
