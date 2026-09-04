from sqlalchemy import text

from database.connection import (
    SessionLocal
)

from database.models import Shelter


SHELTERS = [
    {
        "name": "Greenwich Village Emergency Shelter",
        "latitude": 40.7315,
        "longitude": -74.0015,
        "capacity": 500
    },
    {
        "name": "Washington Square Emergency Center",
        "latitude": 40.7308,
        "longitude": -73.9975,
        "capacity": 750
    },
    {
        "name": "SoHo Community Shelter",
        "latitude": 40.7245,
        "longitude": -74.0000,
        "capacity": 600
    },
    {
        "name": "Chelsea Emergency Shelter",
        "latitude": 40.7380,
        "longitude": -74.0030,
        "capacity": 450
    }
]


def seed_shelters():
    """
    Insert initial shelters if the database
    does not already contain shelters.
    """

    db = SessionLocal()

    try:

        existing_shelters = (
            db.query(Shelter).count()
        )

        if existing_shelters > 0:

            print(
                "Shelters already exist. "
                "Skipping seed operation."
            )

            return

        print(
            "Seeding shelter data..."
        )

        for shelter_data in SHELTERS:

            shelter = Shelter(
                name=shelter_data["name"],
                capacity=shelter_data["capacity"],
                available_capacity=shelter_data[
                    "capacity"
                ],
                is_active=True,
                location=(
                    f"SRID=4326;"
                    f"POINT("
                    f"{shelter_data['longitude']} "
                    f"{shelter_data['latitude']}"
                    f")"
                )
            )

            db.add(shelter)

        db.commit()

        print(
            "Shelter data seeded successfully."
        )

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()