from typing import Any, Literal

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


# --------------------------------------------------
# Assistant request context
# --------------------------------------------------

class AssistantLocation(BaseModel):
    """
    A map location already selected by the user.
    """

    latitude: float = Field(
        ge=-90,
        le=90
    )

    longitude: float = Field(
        ge=-180,
        le=180
    )


class AssistantRouteMetrics(BaseModel):

    total_distance: float = Field(ge=0)
    total_travel_time: float = Field(ge=0)
    average_risk: float = Field(ge=0)
    maximum_risk: float = Field(ge=0)
    road_count: int = Field(ge=0)


class AssistantRouteContext(BaseModel):
    """
    The meaningful part of the route currently shown on the map.

    Coordinates are deliberately not sent to Groq because the
    exact edge IDs and metrics are sufficient for explanation.
    """

    nodes: list[int | str] = Field(
        default_factory=list,
        max_length=5000
    )

    edges: list[
        tuple[
            int | str,
            int | str,
            int | str
        ]
    ] = Field(
        default_factory=list,
        max_length=5000
    )

    total_cost: float = Field(ge=0)

    metrics: AssistantRouteMetrics

    analysis: dict[str, Any] | None = None


class AssistantShelterContext(BaseModel):

    id: int
    name: str
    latitude: float
    longitude: float
    capacity: int = Field(ge=0)
    available_capacity: int = Field(ge=0)
    is_active: bool


class AssistantEvaluatedShelter(BaseModel):

    shelter: AssistantShelterContext
    route: AssistantRouteContext


class AssistantShelterRecommendationContext(
    BaseModel
):

    recommended_shelter: (
        AssistantEvaluatedShelter
        | None
    ) = None

    evaluated_shelters: list[
        AssistantEvaluatedShelter
    ] = Field(
        default_factory=list,
        max_length=100
    )

    analysis: dict[str, Any] | None = None


class AssistantFloodContext(BaseModel):

    active: bool = False
    center: AssistantLocation | None = None
    affected_radius: float | None = Field(
        default=None,
        ge=0
    )
    severe_radius: float | None = Field(
        default=None,
        ge=0
    )
    affected_roads: int | None = Field(
        default=None,
        ge=0
    )
    blocked_roads: int | None = Field(
        default=None,
        ge=0
    )
    state_version: int | None = Field(
        default=None,
        ge=0
    )


class AssistantContext(BaseModel):

    start_location: AssistantLocation | None = None
    destination_location: AssistantLocation | None = None
    route: AssistantRouteContext | None = None
    shelter_recommendation: (
        AssistantShelterRecommendationContext
        | None
    ) = None
    flood: AssistantFloodContext = Field(
        default_factory=AssistantFloodContext
    )


class AssistantHistoryMessage(BaseModel):

    role: Literal[
        "user",
        "assistant"
    ]

    content: str = Field(
        min_length=1,
        max_length=4000
    )


class AssistantChatRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=2000
    )

    context: AssistantContext = Field(
        default_factory=AssistantContext
    )

    history: list[
        AssistantHistoryMessage
    ] = Field(
        default_factory=list,
        max_length=12
    )


class AssistantAction(BaseModel):

    type: Literal[
        "route_calculated",
        "shelter_recommended"
    ]

    payload: dict[str, Any]


class AssistantChatResponse(BaseModel):

    reply: str
    tools_used: list[str] = Field(
        default_factory=list
    )
    actions: list[AssistantAction] = Field(
        default_factory=list
    )
