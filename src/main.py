from graph.osm_loader import load_manhattan_road_network
from graph.road_network import RoadNetwork
from graph.cost_calculator import CostCalculator
from routing.route_engine import RouteEngine


def print_route_results(result, title):
    """
    Print route information in a readable format.
    """

    print(f"\n{title}")
    print("-" * 50)

    if result is None:
        print("No route found.")
        return

    metrics = result["metrics"]

    print(f"Total dynamic cost: {result['total_cost']:.4f}")
    print(f"Nodes in route: {len(result['nodes'])}")
    print(f"Road segments: {metrics['road_count']}")

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


def test_dynamic_rerouting(
    graph,
    road_network,
    route_engine,
    start_node,
    destination_node
):
    """
    Test whether the routing engine finds an alternative
    route after a road on the original route is blocked.
    """

    print("\nDYNAMIC REROUTING TEST")
    print("=" * 50)

    # Find original route
    original_result = route_engine.find_route(
        start_node,
        destination_node
    )

    if original_result is None:
        print("Could not find an initial route.")
        return

    print_route_results(
        original_result,
        "ORIGINAL ROUTE"
    )

    route_edges = original_result["edges"]

    # Choose an edge roughly in the middle of the route
    middle_index = len(route_edges) // 2

    source, target, key = route_edges[middle_index]

    edge_data = graph[source][target][key]

    print("\nSIMULATING ROAD BLOCKAGE")
    print("-" * 50)

    print(
        f"Blocking edge: "
        f"{source} -> {target}"
    )

    print(
        f"Road name: "
        f"{edge_data.get('name', 'Unknown')}"
    )

    print(
        f"Original edge cost: "
        f"{edge_data.get('dynamic_cost', 0):.4f}"
    )

    # Block the exact edge used in the route
    road_network.block_road(
        source,
        target,
        key
    )

    # Find new route
    new_result = route_engine.find_route(
        start_node,
        destination_node
    )

    print_route_results(
        new_result,
        "REROUTED PATH"
    )

    if new_result is None:
        print(
            "\nNo alternative route exists "
            "after blocking this road."
        )
        return

    # Verify blocked edge is not used
    if (source, target, key) not in new_result["edges"]:

        print("\nREROUTING VALIDATION")
        print("-" * 50)
        print(
            "PASS: The routing engine successfully "
            "avoided the blocked road."
        )

    else:
        print(
            "\nFAIL: The blocked road was still "
            "included in the route."
        )


def main():

    print("\nDISASTER EVACUATION ROUTE OPTIMIZER")
    print("=" * 50)

    # --------------------------------------------------
    # 1. Load Manhattan road network
    # --------------------------------------------------

    graph = load_manhattan_road_network()

    print("\nROAD NETWORK")
    print("-" * 50)

    print(
        f"Intersections: "
        f"{graph.number_of_nodes()}"
    )

    print(
        f"Road segments: "
        f"{graph.number_of_edges()}"
    )

    # --------------------------------------------------
    # 2. Initialize disaster-aware road network
    # --------------------------------------------------

    cost_calculator = CostCalculator()

    road_network = RoadNetwork(
        graph,
        cost_calculator
    )

    print(
        "\nInitializing disaster-aware "
        "road attributes..."
    )

    road_network.initialize_edge_attributes()

    print(
        "Calculating dynamic road costs..."
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
    # 4. Select start and destination
    # --------------------------------------------------

    nodes = list(graph.nodes())

    start_node = nodes[0]

    destination_node = nodes[-1]

    print("\nROUTING SCENARIO")
    print("-" * 50)

    print(f"Start node: {start_node}")
    print(
        f"Destination node: "
        f"{destination_node}"
    )

    # --------------------------------------------------
    # 5. Find normal evacuation route
    # --------------------------------------------------

    result = route_engine.find_route(
        start_node,
        destination_node
    )

    print_route_results(
        result,
        "SAFE EVACUATION ROUTE"
    )

    # --------------------------------------------------
    # 6. Test dynamic rerouting
    # --------------------------------------------------

    test_dynamic_rerouting(
        graph,
        road_network,
        route_engine,
        start_node,
        destination_node
    )


if __name__ == "__main__":
    main()