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

from api.schemas import (
    RouteRequest,
    FloodRequest,
    ShelterCreateRequest,
    ShelterRouteRequest
)

from database.init_db import (
    initialize_database
)

from database.seed_data import (
    seed_shelters
)

from services.shelter_service import (
    ShelterService
)

from database.connection import SessionLocal
from database.models import RouteHistory

from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize application resources when
    the FastAPI server starts.
    """

    print(
        "\nStarting Disaster Evacuation Route Optimizer API..."
    )

    initialize_database()
    seed_shelters()

    print("Initializing evacuation service...")

    app.state.evacuation_service = (
        EvacuationService()
    )

    print("Evacuation service ready.")

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
    allow_origins=[
        "http://localhost:5173"
    ],
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

    service.save_route_history(
        start_latitude=request.start_latitude,
        start_longitude=request.start_longitude,
        destination_latitude=(
            request.destination_latitude
        ),
        destination_longitude=(
            request.destination_longitude
        ),
        route_result=result
    )

    return result

@app.get("/routes/history")
def get_route_history():

    db = SessionLocal()

    try:
        routes = (
            db.query(RouteHistory)
            .order_by(RouteHistory.created_at.desc())
            .limit(20)
            .all()
        )

        return {
            "routes": [
                {
                    "id": route.id,
                    "total_distance": route.total_distance,
                    "total_travel_time": route.total_travel_time,
                    "average_risk": route.average_risk,
                    "total_cost": route.total_cost,
                    "created_at": route.created_at
                }
                for route in routes
            ]
        }

    finally:
        db.close()


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

@app.get("/shelters")
def get_shelters():

    shelter_service = ShelterService()

    shelters = (
        shelter_service.get_all_shelters()
    )

    return {
        "shelters": shelters
    }

@app.post("/shelters")
def create_shelter(
    request: ShelterCreateRequest
):

    shelter_service = ShelterService()

    shelter = (
        shelter_service.create_shelter(
            name=request.name,
            latitude=request.latitude,
            longitude=request.longitude,
            capacity=request.capacity
        )
    )

    return {
        "message": (
            "Shelter created successfully."
        ),
        "shelter_id": shelter.id
    }

@app.post("/evacuation/best-shelter")
def find_best_shelter(
    request: ShelterRouteRequest
):

    service = app.state.evacuation_service

    result = (
        service.find_best_shelter(
            request.start_latitude,
            request.start_longitude
        )
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "No reachable evacuation "
                "shelter found."
            )
        )

    return result