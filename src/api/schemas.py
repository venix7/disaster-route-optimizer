from pydantic import BaseModel, Field
from pydantic import (
    BaseModel,
    Field
)


class RouteRequest(BaseModel):
    """
    Request model for evacuation route calculation.
    """

    start_latitude: float
    start_longitude: float

    destination_latitude: float
    destination_longitude: float


class FloodRequest(BaseModel):
    """
    Request model for flood simulation.
    """

    center_latitude: float

    center_longitude: float

    affected_radius: float = Field(
        gt=0,
        description=(
            "Flood affected radius in meters."
        )
    )

    severe_radius: float = Field(
        gt=0,
        description=(
            "Severe flood radius in meters."
        )
    )

class ShelterCreateRequest(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100
    )

    latitude: float

    longitude: float

    capacity: int = Field(
        gt=0
    )


class ShelterResponse(BaseModel):

    id: int

    name: str

    latitude: float

    longitude: float

    capacity: int

    available_capacity: int

    is_active: bool


class ShelterRouteRequest(BaseModel):

    start_latitude: float

    start_longitude: float