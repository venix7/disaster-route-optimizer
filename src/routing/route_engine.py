import heapq
import math


class RouteEngine:

    def __init__(
        self,
        graph,
        road_network
    ):

        self.graph = graph

        self.road_network = road_network


    def find_route(
        self,
        start_node,
        destination_node
    ):
        """
        Find the lowest-cost route using Dijkstra's algorithm.

        Blocked roads are ignored.
        Dynamic road cost is used as the edge weight.
        """

        # Handle same start and destination node
        if start_node == destination_node:

            node_data = self.graph.nodes[
                start_node
            ]

            return {
                "nodes": [start_node],

                "coordinates": [
                    {
                        "latitude":
                            node_data["y"],

                        "longitude":
                            node_data["x"]
                    }
                ],

                "edges": [],

                "total_cost": 0,

                "metrics": {
                    "total_distance": 0,
                    "total_travel_time": 0,
                    "average_risk": 0,
                    "maximum_risk": 0,
                    "road_count": 0
                }
            }


        # Priority queue:
        # (total_cost, node)
        priority_queue = [
            (0, start_node)
        ]


        # Best known cost to each node
        distances = {
            start_node: 0
        }


        # Stores:
        # node -> (previous_node, edge_key)
        previous = {}


        while priority_queue:

            current_cost, current_node = (
                heapq.heappop(
                    priority_queue
                )
            )


            # Skip outdated queue entries
            if (
                current_cost >
                distances.get(
                    current_node,
                    float("inf")
                )
            ):

                continue


            # Destination reached
            if current_node == destination_node:

                break


            # Explore outgoing neighbors
            for neighbor in (
                self.graph.successors(
                    current_node
                )
            ):

                edge_dict = (
                    self.graph.get_edge_data(
                        current_node,
                        neighbor
                    )
                )


                if not edge_dict:

                    continue


                # MultiDiGraph may contain multiple
                # edges between the same nodes
                for key, edge_data in (
                    edge_dict.items()
                ):

                    # Ignore blocked roads
                    if edge_data.get(
                        "blocked",
                        False
                    ):

                        continue


                    edge_cost = (
                        edge_data.get(
                            "dynamic_cost"
                        )
                    )


                    # Ignore invalid costs
                    if (
                        edge_cost is None
                        or not math.isfinite(
                            edge_cost
                        )
                        or edge_cost < 0
                    ):

                        continue


                    new_cost = (
                        current_cost +
                        edge_cost
                    )


                    # Found a cheaper path
                    if (
                        neighbor not in distances
                        or new_cost <
                        distances[neighbor]
                    ):

                        distances[
                            neighbor
                        ] = new_cost


                        # Store exact edge used
                        previous[
                            neighbor
                        ] = (
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


        # -------------------------------------------------
        # No route found
        # -------------------------------------------------

        if destination_node not in distances:

            return None


        # -------------------------------------------------
        # Reconstruct route
        # -------------------------------------------------

        route_nodes, route_edges = (
            self._reconstruct_route(
                previous,
                start_node,
                destination_node
            )
        )


        if route_nodes is None:

            return None


        # -------------------------------------------------
        # Calculate route metrics
        # -------------------------------------------------

        metrics = (
            self.calculate_route_metrics(
                route_edges
            )
        )


        # -------------------------------------------------
        # Convert route nodes to coordinates
        # -------------------------------------------------

        route_coordinates = []


        for node in route_nodes:

            node_data = self.graph.nodes[
                node
            ]


            route_coordinates.append(
                {
                    "latitude":
                        node_data["y"],

                    "longitude":
                        node_data["x"]
                }
            )


        return {

            "nodes":
                route_nodes,

            "coordinates":
                route_coordinates,

            "edges":
                route_edges,

            "total_cost":
                distances[
                    destination_node
                ],

            "metrics":
                metrics

        }


    def find_route_by_coordinates(
        self,
        start_latitude,
        start_longitude,
        destination_latitude,
        destination_longitude
    ):
        """
        Find a route between two exact geographic
        coordinates.

        Instead of relying on only one nearest node,
        multiple nearby start and destination nodes
        are considered.

        This improves routing reliability when the
        closest node is unreachable due to one-way
        roads, disconnected graph sections, or
        blocked roads caused by a disaster.
        """


        # -------------------------------------------------
        # Find nearby candidate start nodes
        # -------------------------------------------------

        start_candidates = (
            self.road_network.find_nearest_nodes(
                start_latitude,
                start_longitude,
                count=5
            )
        )


        # -------------------------------------------------
        # Find nearby candidate destination nodes
        # -------------------------------------------------

        destination_candidates = (
            self.road_network.find_nearest_nodes(
                destination_latitude,
                destination_longitude,
                count=5
            )
        )


        best_route = None

        best_cost = float("inf")


        # -------------------------------------------------
        # Try nearby node combinations
        #
        # 5 start candidates × 5 destination candidates
        # = maximum 25 routing attempts.
        # -------------------------------------------------

        for start_node in start_candidates:

            for destination_node in (
                destination_candidates
            ):

                route = self.find_route(
                    start_node,
                    destination_node
                )


                # This pair is unreachable
                if route is None:

                    continue


                # Keep the lowest-cost reachable route
                if (
                    route["total_cost"]
                    < best_cost
                ):

                    best_route = route

                    best_cost = (
                        route["total_cost"]
                    )


        # -------------------------------------------------
        # No reachable route found
        # -------------------------------------------------

        if best_route is None:

            return None


        # -------------------------------------------------
        # Connect route to exact user-selected locations
        # -------------------------------------------------

        exact_start = {

            "latitude":
                start_latitude,

            "longitude":
                start_longitude

        }


        exact_destination = {

            "latitude":
                destination_latitude,

            "longitude":
                destination_longitude

        }


        road_coordinates = (
            best_route["coordinates"]
        )


        # -------------------------------------------------
        # Final visual route:
        #
        # Exact Start
        #       ↓
        # Selected Start Road Node
        #       ↓
        # Road Network Route
        #       ↓
        # Selected Destination Road Node
        #       ↓
        # Exact Destination
        # -------------------------------------------------

        final_coordinates = (

            [exact_start]

            + road_coordinates

            + [exact_destination]

        )


        best_route["coordinates"] = (
            final_coordinates
        )


        return best_route


    def _reconstruct_route(
        self,
        previous,
        start_node,
        destination_node
    ):
        """
        Reconstruct route nodes and exact edges.
        """

        nodes = [
            destination_node
        ]

        edges = []


        current_node = (
            destination_node
        )


        while current_node != start_node:


            # Safety check for incomplete path
            if current_node not in previous:

                return None, None


            previous_node, edge_key = (
                previous[
                    current_node
                ]
            )


            edges.append(
                (
                    previous_node,
                    current_node,
                    edge_key
                )
            )


            nodes.append(
                previous_node
            )


            current_node = (
                previous_node
            )


        nodes.reverse()

        edges.reverse()


        return (
            nodes,
            edges
        )


    def calculate_route_metrics(
        self,
        route_edges
    ):
        """
        Calculate metrics using the exact edges
        selected by the routing algorithm.
        """

        total_distance = 0

        total_travel_time = 0

        total_risk = 0

        max_risk = 0


        for source, target, key in route_edges:

            edge_data = self.graph[
                source
            ][
                target
            ][
                key
            ]


            total_distance += (
                edge_data.get(
                    "length",
                    0
                )
            )


            travel_time = (
                edge_data.get(
                    "travel_time",
                    0
                )
            )


            # Only include valid travel times
            if math.isfinite(
                travel_time
            ):

                total_travel_time += (
                    travel_time
                )


            risk = (
                edge_data.get(
                    "risk_level",
                    0
                )
            )


            total_risk += risk


            max_risk = max(
                max_risk,
                risk
            )


        road_count = len(
            route_edges
        )


        average_risk = (

            total_risk / road_count

            if road_count > 0

            else 0

        )


        return {

            "total_distance":
                total_distance,

            "total_travel_time":
                total_travel_time,

            "average_risk":
                average_risk,

            "maximum_risk":
                max_risk,

            "road_count":
                road_count

        }