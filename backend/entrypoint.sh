#!/bin/bash
set -e

echo "Waiting for database to be ready..."
# Wait for PostgreSQL if using it
if [ "$DATABASE_TYPE" = "postgres" ]; then
    until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
        echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."
        sleep 2
    done
    echo "PostgreSQL is ready!"
fi

echo "Running Alembic migrations..."
alembic upgrade head

echo "Checking if sample data should be seeded..."
if [ "$SEED_SAMPLE_DATA" = "true" ]; then
    echo "Seeding sample websites..."
    python -c "
from app.core.database import SessionLocal
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    db = SessionLocal()
    # TODO: Add sample website seeding logic here when models are defined
    # Example:
    # from app.models.website import Website
    # existing = db.query(Website).count()
    # if existing == 0:
    #     sample_sites = [
    #         Website(name='Example', url='https://example.com'),
    #         Website(name='Test Site', url='https://test.com'),
    #     ]
    #     db.add_all(sample_sites)
    #     db.commit()
    #     logger.info(f'Seeded {len(sample_sites)} sample websites')
    # else:
    #     logger.info(f'Database already has {existing} websites, skipping seed')
    logger.info('Sample data seeding completed (no models to seed yet)')
    db.close()
except Exception as e:
    logger.error(f'Error seeding data: {e}')
    raise
" || echo "Seeding skipped or failed (this is okay if no models exist yet)"
fi

echo "Starting application..."
exec "$@"
