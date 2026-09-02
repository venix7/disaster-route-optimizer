from graph.osm_loader import load_manhattan_road_network
from graph.road_network import RoadNetwork
import osmnx as ox


def main():
    graph = load_manhattan_road_network()

    road_network = RoadNetwork(graph)

    # Basic statistics
    stats = road_network.get_statistics()

    print("\nROAD NETWORK STATISTICS")
    print("-" * 40)

    for key, value in stats.items():
        print(f"{key}: {value}")

    # Sample node
    node_id = next(iter(graph.nodes))

    coordinates = road_network.get_node_coordinates(node_id)

    print("\nSAMPLE NODE")
    print("-" * 40)
    print(f"Node ID: {node_id}")
    print(f"Latitude: {coordinates['latitude']}")
    print(f"Longitude: {coordinates['longitude']}")

    print("\nGenerating road network visualization...")

    ox.plot_graph(
        graph,
        node_size=0,
        edge_linewidth=0.8,
        show=True,
        close=True
    )


if __name__ == "__main__":
    main()