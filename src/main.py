from graph.osm_loader import load_manhattan_road_network
from graph.road_network import RoadNetwork
from graph.cost_calculator import CostCalculator
from routing.route_engine import RouteEngine
from disaster.flood_simulator import FloodSimulator


def print_route_results(result, title):
    """
    Print route information.
    """

    print(f"\n{title}")
    print("-" * 50)

    if result is None:
        print("No route found.")
        return

    metrics = result["metrics"]

    print(
        f"Total dynamic cost: "
        f"{result['total_cost']:.4f}"
    )

    print(
        f"Nodes in route: "
        f"{len(result['nodes'])}"
    )

    print(
        f"Road segments: "
        f"{metrics['road_count']}"
    )

    print(
        f"Total distance: "
        f"{metrics['total_distance']:.2f} meters"
    )

    print(
        f"Estimated travel time: "
        f"{metrics['total_travel_time']:.2f} seconds"
    )

    print(
        f"Average risk: "
        f"{metrics['average_risk']:.3f}"
    )

    print(
        f"Maximum risk: "
        f"{metrics['maximum_risk']:.3f}"
    )


def main():

    print("\nDISASTER EVACUATION ROUTE OPTIMIZER")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Load road network
    # --------------------------------------------------

    graph = load_manhattan_road_network()

    print("\nROAD NETWORK")
    print("-" * 60)

    print(
        f"Intersections: "
        f"{graph.number_of_nodes()}"
    )

    print(
        f"Road segments: "
        f"{graph.number_of_edges()}"
    )

    # --------------------------------------------------
    # 2. Initialize disaster-aware graph
    # --------------------------------------------------

    cost_calculator = CostCalculator()

    road_network = RoadNetwork(
        graph,
        cost_calculator
    )

    print(
        "\nInitializing road attributes..."
    )

    road_network.initialize_edge_attributes()

    print(
        "Calculating dynamic costs..."
    )

    road_network.calculate_dynamic_costs()

    # --------------------------------------------------
    # 3. Create routing engine
    # --------------------------------------------------

    route_engine = RouteEngine(
        graph,
        road_network
    )

    # --------------------------------------------------
    # 4. Create flood simulator
    # --------------------------------------------------

    flood_simulator = FloodSimulator(
        road_network
    )

    # --------------------------------------------------
    # 5. Select routing scenario
    # --------------------------------------------------

    nodes = list(graph.nodes())

    start_node = nodes[0]

    destination_node = nodes[-1]

    print("\nEVACUATION SCENARIO")
    print("-" * 60)

    print(
        f"Start node: {start_node}"
    )

    print(
        f"Destination node: "
        f"{destination_node}"
    )

    # --------------------------------------------------
    # 6. Find normal route
    # --------------------------------------------------

    normal_route = route_engine.find_route(
        start_node,
        destination_node
    )

    print_route_results(
        normal_route,
        "NORMAL ROUTE (NO DISASTER)"
    )

    # --------------------------------------------------
    # 7. Create flood event
    # --------------------------------------------------

    # Choose the midpoint node from the normal route
    # as the flood center so the disaster is guaranteed
    # to affect the evacuation path.

    route_nodes = normal_route["nodes"]

    flood_node = route_nodes[
        len(route_nodes) // 2
    ]

    flood_node_data = graph.nodes[flood_node]

    flood_latitude = flood_node_data["y"]
    flood_longitude = flood_node_data["x"]

    print("\nSIMULATING FLOOD EVENT")
    print("-" * 60)

    print(
        f"Flood center node: {flood_node}"
    )

    print(
        f"Latitude: {flood_latitude}"
    )

    print(
        f"Longitude: {flood_longitude}"
    )

    # --------------------------------------------------
    # 8. Apply flood
    # --------------------------------------------------

    flood_result = flood_simulator.simulate_flood(
        center_latitude=flood_latitude,
        center_longitude=flood_longitude,

        # Roads within 500m are affected
        affected_radius=500,

        # Roads within 150m are severely flooded
        severe_radius=150
    )

    print("\nFLOOD IMPACT")
    print("-" * 60)

    print(
        f"Affected roads: "
        f"{flood_result['affected_roads']}"
    )

    print(
        f"Blocked roads: "
        f"{flood_result['blocked_roads']}"
    )

    # --------------------------------------------------
    # 9. Find disaster-aware route
    # --------------------------------------------------

    disaster_route = route_engine.find_route(
        start_node,
        destination_node
    )

    print_route_results(
        disaster_route,
        "DISASTER-AWARE EVACUATION ROUTE"
    )

    # --------------------------------------------------
    # 10. Compare routes
    # --------------------------------------------------

    if disaster_route is not None:

        normal_metrics = normal_route["metrics"]

        disaster_metrics = disaster_route[
            "metrics"
        ]

        print("\nROUTE COMPARISON")
        print("=" * 60)

        distance_difference = (
            disaster_metrics["total_distance"]
            - normal_metrics["total_distance"]
        )

        time_difference = (
            disaster_metrics["total_travel_time"]
            - normal_metrics["total_travel_time"]
        )

        cost_difference = (
            disaster_route["total_cost"]
            - normal_route["total_cost"]
        )

        print(
            f"Distance difference: "
            f"{distance_difference:.2f} meters"
        )

        print(
            f"Travel time difference: "
            f"{time_difference:.2f} seconds"
        )

        print(
            f"Cost difference: "
            f"{cost_difference:.4f}"
        )

        print(
            f"\nNormal route risk: "
            f"{normal_metrics['average_risk']:.3f}"
        )

        print(
            f"Evacuation route risk: "
            f"{disaster_metrics['average_risk']:.3f}"
        )


if __name__ == "__main__":
    main()