from sqlalchemy import text

from database.connection import (
    SessionLocal
)

from database.models import Shelter


class ShelterService:

    def get_all_shelters(self):
        """
        Retrieve all active shelters.
        """

        db = SessionLocal()

        try:

            shelters = (
                db.query(Shelter)
                .filter(
                    Shelter.is_active == True
                )
                .all()
            )

            result = []

            for shelter in shelters:

                coordinates = db.execute(
                    text(
                        """
                        SELECT
                            ST_Y(location::geometry),
                            ST_X(location::geometry)
                        FROM shelters
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": shelter.id
                    }
                ).fetchone()

                result.append(
                    {
                        "id": shelter.id,
                        "name": shelter.name,
                        "latitude": coordinates[0],
                        "longitude": coordinates[1],
                        "capacity": shelter.capacity,
                        "available_capacity": (
                            shelter.available_capacity
                        ),
                        "is_active": shelter.is_active
                    }
                )

            return result

        finally:

            db.close()


    def create_shelter(
        self,
        name,
        latitude,
        longitude,
        capacity
    ):
        """
        Create a new shelter.
        """

        db = SessionLocal()

        try:

            shelter = Shelter(
                name=name,
                capacity=capacity,
                available_capacity=capacity,
                is_active=True,
                location=(
                    f"SRID=4326;"
                    f"POINT("
                    f"{longitude} {latitude}"
                    f")"
                )
            )

            db.add(shelter)

            db.commit()

            db.refresh(shelter)

            return shelter

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()