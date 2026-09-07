from graph.osm_loader import load_manhattan_road_network
from graph.road_network import RoadNetwork
from graph.cost_calculator import CostCalculator
from routing.route_engine import RouteEngine
from disaster.flood_simulator import FloodSimulator
from services.shelter_service import ShelterService
from services.route_analysis_service import (
    RouteAnalysisService
)
from database.connection import SessionLocal
from database.models import RouteHistory


class EvacuationService:
    def __init__(self):
        """
        Initialize the disaster evacuation system.
        """

        print(
            "Initializing evacuation service..."
        )

        # Load Manhattan road network
        self.graph = (
            load_manhattan_road_network()
        )

        # Initialize cost calculation system
        self.cost_calculator = (
            CostCalculator()
        )

        # Initialize road network manager
        self.road_network = RoadNetwork(
            self.graph,
            self.cost_calculator
        )

        print(
            "Initializing road attributes..."
        )

        self.road_network.initialize_edge_attributes()

        print(
            "Calculating dynamic costs..."
        )

        self.road_network.calculate_dynamic_costs()

        # Initialize routing engine
        self.route_engine = RouteEngine(
            self.graph,
            self.road_network
        )

        # Initialize disaster simulator
        self.flood_simulator = FloodSimulator(
            self.road_network
        )

        # Deterministic facts used by the natural-language
        # assistant. This service reads the same live graph
        # and never replaces the routing algorithm.
        self.route_analysis_service = (
            RouteAnalysisService(
                self.graph,
                self.road_network,
                self.route_engine
            )
        )

        print(
            "Evacuation service ready."
        )

    def get_network_info(self):
        """
        Return information about the road network.
        """

        return {
            "intersections": (
                self.graph.number_of_nodes()
            ),
            "road_segments": (
                self.graph.number_of_edges()
            )
        }

    def _add_route_coordinates(
        self,
        route_result
    ):
        """
        Add latitude and longitude coordinates
        for each node in the calculated route.
        """

        if route_result is None:
            return None

        coordinates = []

        for node in route_result["nodes"]:

            node_data = self.graph.nodes[node]

            coordinates.append(
                {
                    "latitude": node_data["y"],
                    "longitude": node_data["x"]
                }
            )

        route_result["coordinates"] = coordinates

        return route_result
    
    def find_route(
        self,
        start_latitude,
        start_longitude,
        destination_latitude,
        destination_longitude
    ):
        """
        Find an evacuation route using geographic coordinates.
        """

        route_result = (
            self.route_engine
            .find_route_by_coordinates(
                start_latitude,
                start_longitude,
                destination_latitude,
                destination_longitude
            )
        )

        route_result = self._add_route_coordinates(
            route_result
        )

        return self._add_route_analysis(
            route_result
        )

    def simulate_flood(
        self,
        center_latitude,
        center_longitude,
        affected_radius,
        severe_radius
    ):
        """
        Simulate a geographic flood event.
        """

        return self.flood_simulator.simulate_flood(
            center_latitude,
            center_longitude,
            affected_radius,
            severe_radius
        )

    def reset_disaster(self):
        """
        Reset all disaster conditions.
        """

        self.flood_simulator.reset_disaster()

        return {
            "message": (
                "Disaster conditions reset successfully."
            )
        }

    def get_hazard_status(self):
        """
        Return the current deterministic flood and road state.
        """

        return self.flood_simulator.get_hazard_status()

    def find_best_shelter(
        self,
        start_latitude,
        start_longitude
    ):
        """
        Evaluate routes to all available shelters
        and select the shelter with the lowest
        evacuation cost.
        """

        shelter_service = ShelterService()

        shelters = (
            shelter_service.get_all_shelters()
        )

        best_result = None

        evaluated_shelters = []

        for shelter in shelters:

            # An active shelter with no remaining space is not
            # an available evacuation destination.
            if shelter.get(
                "available_capacity",
                0
            ) <= 0:
                continue

            route_result = (
                self.route_engine
                .find_route_by_coordinates(
                    start_latitude,
                    start_longitude,
                    shelter["latitude"],
                    shelter["longitude"]
                )
            )

            route_result = self._add_route_coordinates(
                route_result
            )

            if route_result is None:
                continue

            shelter_result = {
                "shelter": shelter,
                "route": route_result
            }

            evaluated_shelters.append(
                shelter_result
            )

            if (
                best_result is None
                or route_result["total_cost"]
                < best_result["route"]["total_cost"]
            ):

                best_result = shelter_result

        if best_result is None:

            return None

        best_result["route"] = (
            self._add_route_analysis(
                best_result["route"]
            )
        )

        recommendation_result = {
            "recommended_shelter": (
                best_result
            ),
            "evaluated_shelters": (
                evaluated_shelters
            )
        }

        recommendation_result["analysis"] = (
            self.route_analysis_service
            .analyze_shelter_recommendation(
                recommendation_result
            )
        )

        return recommendation_result

    def _add_route_analysis(
        self,
        route_result
    ):
        """
        Attach an explainability snapshot at calculation time.

        Keeping this snapshot with the route prevents a later
        flood update from silently changing the facts used to
        explain why the displayed route was selected.
        """

        if route_result is None:
            return None

        route_result["analysis"] = (
            self.route_analysis_service.analyze_route(
                route_result,
                self.get_hazard_status()
            )
        )

        return route_result

    def save_route_history(
        self,
        start_latitude,
        start_longitude,
        destination_latitude,
        destination_longitude,
        route_result
    ):
        """
        Save calculated route information
        to PostgreSQL.
        """

        db = SessionLocal()

        try:

            metrics = (
                route_result["metrics"]
            )

            route_history = RouteHistory(
                start_latitude=start_latitude,
                start_longitude=start_longitude,
                destination_latitude=(
                    destination_latitude
                ),
                destination_longitude=(
                    destination_longitude
                ),
                total_distance=(
                    metrics["total_distance"]
                ),
                total_travel_time=(
                    metrics["total_travel_time"]
                ),
                average_risk=(
                    metrics["average_risk"]
                ),
                total_cost=(
                    route_result["total_cost"]
                )
            )

            db.add(route_history)

            db.commit()

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()
