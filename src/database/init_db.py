from sqlalchemy import text

from database.connection import (
    engine,
    Base
)

import database.models


def initialize_database():
    """
    Enable PostGIS and create database tables.
    """

    print(
        "Initializing PostgreSQL/PostGIS database..."
    )

    with engine.connect() as connection:

        connection.execute(
            text(
                "CREATE EXTENSION IF NOT EXISTS postgis"
            )
        )

        connection.commit()

    Base.metadata.create_all(
        bind=engine
    )

    print(
        "Database initialization complete."
    )