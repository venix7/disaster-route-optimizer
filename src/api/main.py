import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    JSONResponse
)
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from api.schemas import (
    RouteRequest,
    FloodRequest,
    ShelterCreateRequest,
    ShelterRouteRequest,
    AssistantChatRequest,
    AssistantChatResponse
)

from services.evacuation_service import (
    EvacuationService
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

from database.connection import (
    SessionLocal,
    check_database_connection,
    engine,
    wait_for_database
)
from database.models import RouteHistory
from llm.assistant_service import (
    AssistantService,
    AssistantServiceError
)
from llm.config import (
    AssistantConfigurationError
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

    app.state.ready = False

    wait_for_database()
    initialize_database()
    seed_shelters()

    print("Initializing evacuation service...")

    app.state.evacuation_service = (
        EvacuationService()
    )

    app.state.assistant_service = (
        AssistantService(
            app.state.evacuation_service
        )
    )

    app.state.ready = True

    print("Evacuation service ready.")

    yield

    app.state.ready = False
    engine.dispose()

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

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

configured_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        ""
    ).split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        default_origins
        + configured_origins
    ),
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
    Check whether the API and database are ready.
    """

    service_ready = bool(
        getattr(
            app.state,
            "ready",
            False
        )
    )

    if not service_ready:
        return JSONResponse(
            status_code=503,
            content={
                "status": "starting",
                "database": "unknown"
            }
        )

    try:
        check_database_connection()

    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "unavailable"
            }
        )

    return {
        "status": "healthy",
        "database": "connected",
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


# --------------------------------------------------
# Natural-Language Assistant
# --------------------------------------------------

@app.post(
    "/assistant/chat",
    response_model=AssistantChatResponse
)
def assistant_chat(
    request: AssistantChatRequest
):
    """
    Let Groq select deterministic evacuation tools and
    explain their structured results.
    """

    assistant_service = (
        app.state.assistant_service
    )

    if not assistant_service.is_configured:

        raise HTTPException(
            status_code=503,
            detail=(
                "The assistant is not configured. "
                "Set GROQ_API_KEY on the backend."
            )
        )

    try:

        return assistant_service.chat(
            message=request.message,
            context=request.context.model_dump(
                mode="python",
                exclude_none=True
            ),
            history=[
                item.model_dump(
                    mode="python"
                )
                for item in request.history
            ]
        )

    except AssistantConfigurationError:

        raise HTTPException(
            status_code=503,
            detail=(
                "The assistant is not configured. "
                "Set GROQ_API_KEY on the backend."
            )
        )

    except AssistantServiceError:

        raise HTTPException(
            status_code=502,
            detail=(
                "Groq could not complete the request. "
                "The deterministic routing endpoints remain "
                "available."
            )
        )


# --------------------------------------------------
# Compiled React Frontend
# --------------------------------------------------

FRONTEND_DIST_DIR = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "dist"
)

FRONTEND_INDEX_FILE = (
    FRONTEND_DIST_DIR
    / "index.html"
)


if FRONTEND_INDEX_FILE.exists():

    frontend_assets = (
        FRONTEND_DIST_DIR
        / "assets"
    )

    if frontend_assets.is_dir():
        app.mount(
            "/assets",
            StaticFiles(
                directory=frontend_assets
            ),
            name="frontend-assets"
        )

    @app.get(
        "/",
        include_in_schema=False
    )
    def serve_frontend_index():
        """Serve the compiled React entry page."""

        return FileResponse(
            FRONTEND_INDEX_FILE
        )

    @app.get(
        "/{requested_path:path}",
        include_in_schema=False
    )
    def serve_frontend_path(
        requested_path: str
    ):
        """Serve a frontend file or fall back to React's entry page."""

        requested_file = (
            FRONTEND_DIST_DIR
            / requested_path
        ).resolve()

        frontend_root = (
            FRONTEND_DIST_DIR.resolve()
        )

        if (
            requested_file.is_file()
            and frontend_root
            in requested_file.parents
        ):
            return FileResponse(
                requested_file
            )

        return FileResponse(
            FRONTEND_INDEX_FILE
        )

else:

    @app.get(
        "/",
        include_in_schema=False
    )
    def api_root():
        """Describe local API mode when no React build is present."""

        return {
            "service": (
                "Disaster Evacuation Route Optimizer"
            ),
            "docs": "/docs",
            "frontend": "Run the Vite development server."
        }
