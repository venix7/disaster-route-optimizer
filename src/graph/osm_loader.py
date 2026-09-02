from pathlib import Path
import osmnx as ox


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data directory
DATA_DIR = PROJECT_ROOT / "data"

# Saved graph file
GRAPH_FILE = DATA_DIR / "manhattan_graph.graphml"


def load_manhattan_road_network():
    """
    Load the Manhattan road network from a local GraphML file.
    If it does not exist, download it from OpenStreetMap and save it.
    """

    if GRAPH_FILE.exists():
        print("Loading existing Manhattan road network...")
        graph = ox.load_graphml(GRAPH_FILE)

    else:
        print("Downloading Manhattan road network from OpenStreetMap...")

        # Selected Manhattan region
        north = 40.775
        south = 40.720
        east = -73.985
        west = -74.015

        graph = ox.graph_from_bbox(
            bbox=(west, south, east, north),
            network_type="drive"
        )

        DATA_DIR.mkdir(exist_ok=True)

        ox.save_graphml(graph, GRAPH_FILE)

        print(f"Graph saved to {GRAPH_FILE}")

    return graph