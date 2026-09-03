from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    RouteRequest,
    FloodRequest
)

from services.evacuation_service import (
    EvacuationService
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize application resources when
    the FastAPI server starts.
    """

    print(
        "\nStarting Disaster Evacuation Route Optimizer API..."
    )

    app.state.evacuation_service = (
        EvacuationService()
    )

    yield

    print(
        "\nShutting down Disaster Evacuation Route Optimizer API..."
    )


app = FastAPI(
    title="Disaster Evacuation Route Optimizer",
    description=(
        "API for disaster-aware evacuation routing "
        "and flood simulation."
    ),
    version="1.0.0",
    lifespan=lifespan
)


# --------------------------------------------------
# CORS Configuration
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health")
def health_check():
    """
    Check whether the API is running.
    """

    return {
        "status": "healthy",
        "service": (
            "Disaster Evacuation Route Optimizer"
        )
    }


# --------------------------------------------------
# Network Information
# --------------------------------------------------

@app.get("/network/info")
def get_network_info():

    service = app.state.evacuation_service

    return service.get_network_info()


# --------------------------------------------------
# Route Calculation
# --------------------------------------------------

@app.post("/route")
def find_evacuation_route(
    request: RouteRequest
):
    """
    Find the lowest-cost evacuation route.
    """

    service = app.state.evacuation_service

    result = service.find_route(
        start_latitude=request.start_latitude,
        start_longitude=request.start_longitude,
        destination_latitude=(
            request.destination_latitude
        ),
        destination_longitude=(
            request.destination_longitude
        )
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="No evacuation route found."
        )

    return result


# --------------------------------------------------
# Flood Simulation
# --------------------------------------------------

@app.post("/disaster/flood")
def simulate_flood(
    request: FloodRequest
):
    """
    Simulate a flood event and update
    road conditions.
    """

    # Severe radius should not exceed
    # the affected radius
    if (
        request.severe_radius
        > request.affected_radius
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Severe radius cannot be greater "
                "than affected radius."
            )
        )

    service = app.state.evacuation_service

    result = service.simulate_flood(
        center_latitude=request.center_latitude,
        center_longitude=request.center_longitude,
        affected_radius=request.affected_radius,
        severe_radius=request.severe_radius
    )

    return {
        "message": (
            "Flood simulation applied successfully."
        ),
        "flood_impact": result
    }


# --------------------------------------------------
# Reset Disaster Conditions
# --------------------------------------------------

@app.post("/disaster/reset")
def reset_disaster():

    service = app.state.evacuation_service

    return service.reset_disaster()