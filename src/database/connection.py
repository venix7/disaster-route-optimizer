import os
import time

from dotenv import load_dotenv

from sqlalchemy import (
    create_engine,
    text
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker
)
from sqlalchemy.pool import NullPool


load_dotenv()


def _read_positive_integer(
    variable_name,
    default
):
    """Read a positive integer without making optional settings fatal."""

    raw_value = os.getenv(
        variable_name
    )

    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        return default

    return value if value > 0 else default


def normalize_database_url(database_url):
    """
    Make standard PostgreSQL URLs use the installed psycopg v3 driver.

    Neon and Railway normally provide ``postgresql://`` URLs, while
    SQLAlchemy otherwise assumes the older psycopg2 driver.
    """

    if database_url.startswith(
        "postgres://"
    ):
        return database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1
        )

    if database_url.startswith(
        "postgresql://"
    ):
        return database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1
        )

    return database_url


RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not RAW_DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set."
    )


DATABASE_URL = normalize_database_url(
    RAW_DATABASE_URL
)

DB_CONNECT_TIMEOUT_SECONDS = (
    _read_positive_integer(
        "DB_CONNECT_TIMEOUT_SECONDS",
        10
    )
)

DB_RETRY_ATTEMPTS = _read_positive_integer(
    "DB_RETRY_ATTEMPTS",
    8
)

DB_RETRY_DELAY_SECONDS = (
    _read_positive_integer(
        "DB_RETRY_DELAY_SECONDS",
        2
    )
)


engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={
        "connect_timeout": (
            DB_CONNECT_TIMEOUT_SECONDS
        )
    },
    # Railway can only sleep after outbound traffic stops. Neon already
    # provides an optional PgBouncer endpoint, so holding a second pool
    # of idle connections inside this low-traffic app is unnecessary.
    poolclass=NullPool
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def check_database_connection():
    """Run a small query and raise when PostgreSQL is unavailable."""

    with engine.connect() as connection:
        connection.execute(
            text("SELECT 1")
        )


def wait_for_database():
    """
    Wait for PostgreSQL during startup.

    This covers a Neon cold start and short network interruptions without
    hiding a permanently invalid connection string.
    """

    for attempt in range(
        1,
        DB_RETRY_ATTEMPTS + 1
    ):

        try:
            check_database_connection()

            print(
                "Database connection ready."
            )

            return

        except SQLAlchemyError as error:

            if attempt == DB_RETRY_ATTEMPTS:
                raise RuntimeError(
                    "Could not connect to PostgreSQL after "
                    f"{DB_RETRY_ATTEMPTS} attempts."
                ) from error

            delay_seconds = min(
                DB_RETRY_DELAY_SECONDS
                * (2 ** (attempt - 1)),
                10
            )

            print(
                "Database is not ready "
                f"(attempt {attempt}/"
                f"{DB_RETRY_ATTEMPTS}). "
                f"Retrying in {delay_seconds} seconds..."
            )

            time.sleep(
                delay_seconds
            )


def get_db():
    """
    Provide a database session.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
