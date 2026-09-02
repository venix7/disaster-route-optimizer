from graph.osm_loader import load_manhattan_road_network
from graph.road_network import RoadNetwork
from graph.cost_calculator import CostCalculator


def validate_cost_system(cost_calculator):
    """
    Test whether emergency risk weighting prioritizes safer roads.
    """

    road_a_cost = cost_calculator.calculate_cost(
        normalized_distance=0.3,
        normalized_time=0.3,
        traffic_level=0.2,
        risk_level=0.9
    )

    road_b_cost = cost_calculator.calculate_cost(
        normalized_distance=0.6,
        normalized_time=0.6,
        traffic_level=0.2,
        risk_level=0.1
    )

    print("\nCOST SYSTEM VALIDATION")
    print("-" * 40)

    print(f"Road A (Short, High Risk): {road_a_cost:.4f}")
    print(f"Road B (Longer, Low Risk): {road_b_cost:.4f}")

    if road_b_cost < road_a_cost:
        print("PASS: Safer road is preferred.")
    else:
        print("FAIL: Cost weights need adjustment.")


def main():
    # Load graph
    graph = load_manhattan_road_network()

    # Create components
    cost_calculator = CostCalculator()
    road_network = RoadNetwork(graph, cost_calculator)

    # Initialize disaster-aware attributes
    print("\nInitializing road attributes...")
    road_network.initialize_edge_attributes()

    # Calculate initial costs
    print("Calculating dynamic road costs...")
    road_network.calculate_dynamic_costs()

    # Validate entire graph
    validation = road_network.validate_edge_attributes()

    print("\nGRAPH ATTRIBUTE VALIDATION")
    print("-" * 40)
    print(f"Total roads: {validation['total_edges']}")
    print(f"Missing attributes: {validation['missing_attributes']}")
    print(f"Graph valid: {validation['valid']}")

    # Validate cost behavior
    validate_cost_system(cost_calculator)

    # Demonstrate dynamic update
    source, target, key, edge_data = next(
        iter(graph.edges(keys=True, data=True))
    )

    original_cost = edge_data["dynamic_cost"]

    print("\nDYNAMIC UPDATE DEMONSTRATION")
    print("-" * 40)
    print(f"Road: {edge_data.get('name', 'Unknown')}")
    print(f"Original risk: {edge_data['risk_level']:.2f}")
    print(f"Original cost: {original_cost:.4f}")

    # Simulate hazard
    road_network.update_road_risk(
        source,
        target,
        key,
        risk_level=0.8
    )

    updated_edge = graph[source][target][key]

    print(f"\nUpdated risk: {updated_edge['risk_level']:.2f}")
    print(f"Updated cost: {updated_edge['dynamic_cost']:.4f}")

    # Block road
    road_network.block_road(source, target, key)

    print(f"\nRoad blocked: {updated_edge['blocked']}")


if __name__ == "__main__":
    main()