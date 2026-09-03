from graph.osm_loader import load_manhattan_road_network
from graph.road_network import RoadNetwork
from graph.cost_calculator import CostCalculator
from routing.route_engine import RouteEngine
from disaster.flood_simulator import FloodSimulator


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

        return (
            self.route_engine
            .find_route_by_coordinates(
                start_latitude,
                start_longitude,
                destination_latitude,
                destination_longitude
            )
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