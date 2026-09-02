import osmnx as ox


class RoadNetwork:
    def __init__(self, graph):
        self.graph = graph

    def get_statistics(self):
        """Return basic statistics about the road network."""
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "graph_type": type(self.graph).__name__,
        }

    def get_node_coordinates(self, node_id):
        """Return latitude and longitude of a node."""
        node = self.graph.nodes[node_id]

        return {
            "latitude": node["y"],
            "longitude": node["x"],
        }

    def get_edge_data(self, source, target, key=0):
        """Return data for a specific road segment."""
        return self.graph.get_edge_data(source, target, key)

    def find_nearest_node(self, latitude, longitude):
        """Find the closest road network node to a geographic location."""
        return ox.distance.nearest_nodes(
            self.graph,
            X=longitude,
            Y=latitude
        )