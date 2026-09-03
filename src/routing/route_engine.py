import heapq


class RouteEngine:
    def __init__(self, graph, road_network):
        self.graph = graph
        self.road_network = road_network

    def find_route(self, start_node, destination_node):
        """
        Find the lowest-cost route using Dijkstra's algorithm.

        Blocked roads are ignored.
        Dynamic road cost is used as the edge weight.
        """

        priority_queue = [(0, start_node)]

        distances = {
            start_node: 0
        }

        # Stores:
        # node -> (previous_node, edge_key)
        previous = {}

        visited = set()

        while priority_queue:

            current_cost, current_node = heapq.heappop(
                priority_queue
            )

            if current_node in visited:
                continue

            visited.add(current_node)

            if current_node == destination_node:
                break

            for neighbor in self.graph.successors(current_node):

                edge_dict = self.graph.get_edge_data(
                    current_node,
                    neighbor
                )

                if not edge_dict:
                    continue

                # MultiDiGraph may have multiple edges
                # between the same nodes
                for key, edge_data in edge_dict.items():

                    # Ignore blocked roads
                    if edge_data.get("blocked", False):
                        continue

                    edge_cost = edge_data.get(
                        "dynamic_cost",
                        float("inf")
                    )

                    new_cost = (
                        current_cost + edge_cost
                    )

                    if (
                        neighbor not in distances
                        or new_cost < distances[neighbor]
                    ):

                        distances[neighbor] = new_cost

                        # Store both node and exact edge
                        previous[neighbor] = (
                            current_node,
                            key
                        )

                        heapq.heappush(
                            priority_queue,
                            (
                                new_cost,
                                neighbor
                            )
                        )

        # No route found
        if destination_node not in distances:
            return None

        # Reconstruct exact route
        route_nodes, route_edges = (
            self._reconstruct_route(
                previous,
                start_node,
                destination_node
            )
        )

        metrics = self.calculate_route_metrics(
            route_edges
        )

        return {
            "nodes": route_nodes,
            "edges": route_edges,
            "total_cost": distances[destination_node],
            "metrics": metrics
        }

    def find_route_by_coordinates(
        self,
        start_latitude,
        start_longitude,
        destination_latitude,
        destination_longitude
    ):
        """
        Find a route using geographic coordinates.
        """

        start_node = (
            self.road_network.find_nearest_node(
                start_latitude,
                start_longitude
            )
        )

        destination_node = (
            self.road_network.find_nearest_node(
                destination_latitude,
                destination_longitude
            )
        )

        return self.find_route(
            start_node,
            destination_node
        )

    def _reconstruct_route(
        self,
        previous,
        start_node,
        destination_node
    ):
        """
        Reconstruct route nodes and exact edges.
        """

        nodes = [destination_node]
        edges = []

        current_node = destination_node

        while current_node != start_node:

            previous_node, edge_key = (
                previous[current_node]
            )

            edges.append(
                (
                    previous_node,
                    current_node,
                    edge_key
                )
            )

            nodes.append(previous_node)

            current_node = previous_node

        nodes.reverse()
        edges.reverse()

        return nodes, edges

    def calculate_route_metrics(self, route_edges):
        """
        Calculate metrics using the exact edges
        selected by the routing algorithm.
        """

        total_distance = 0
        total_travel_time = 0
        total_risk = 0
        max_risk = 0

        for source, target, key in route_edges:

            edge_data = (
                self.graph[source][target][key]
            )

            total_distance += edge_data.get(
                "length",
                0
            )

            total_travel_time += edge_data.get(
                "travel_time",
                0
            )

            risk = edge_data.get(
                "risk_level",
                0
            )

            total_risk += risk

            max_risk = max(
                max_risk,
                risk
            )

        road_count = len(route_edges)

        average_risk = (
            total_risk / road_count
            if road_count > 0
            else 0
        )

        return {
            "total_distance": total_distance,
            "total_travel_time": total_travel_time,
            "average_risk": average_risk,
            "maximum_risk": max_risk,
            "road_count": road_count
        }