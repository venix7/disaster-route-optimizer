from pydantic import BaseModel, Field


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