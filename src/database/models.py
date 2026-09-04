from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Boolean,
    DateTime
)

from geoalchemy2 import Geometry

from database.connection import Base


class Shelter(Base):

    __tablename__ = "shelters"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    capacity = Column(
        Integer,
        nullable=False
    )

    available_capacity = Column(
        Integer,
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True
    )

    location = Column(
        Geometry(
            geometry_type="POINT",
            srid=4326
        ),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class DisasterEvent(Base):

    __tablename__ = "disaster_events"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    disaster_type = Column(
        String,
        nullable=False
    )

    severity = Column(
        Float,
        nullable=False
    )

    location = Column(
        Geometry(
            geometry_type="POINT",
            srid=4326
        ),
        nullable=False
    )

    affected_radius = Column(
        Float,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class RouteHistory(Base):

    __tablename__ = "route_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    start_latitude = Column(
        Float,
        nullable=False
    )

    start_longitude = Column(
        Float,
        nullable=False
    )

    destination_latitude = Column(
        Float,
        nullable=False
    )

    destination_longitude = Column(
        Float,
        nullable=False
    )

    total_distance = Column(
        Float
    )

    total_travel_time = Column(
        Float
    )

    average_risk = Column(
        Float
    )

    total_cost = Column(
        Float
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )