import osmnx as ox
import random

from graph.cost_calculator import CostCalculator


class RoadNetwork:

    def __init__(
        self,
        graph,
        cost_calculator=None
    ):

        self.graph = graph
        self.cost_calculator = cost_calculator

        self.max_distance = None
        self.max_travel_time = None


    def get_statistics(self):
        """Return basic statistics about the road network."""

        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "graph_type": type(
                self.graph
            ).__name__,
        }


    def get_node_coordinates(
        self,
        node_id
    ):
        """Return latitude and longitude of a node."""

        node = self.graph.nodes[
            node_id
        ]

        return {
            "latitude": node["y"],
            "longitude": node["x"],
        }


    def get_edge_data(
        self,
        source,
        target,
        key=0
    ):
        """Return data for a specific road segment."""

        return self.graph.get_edge_data(
            source,
            target,
            key
        )


    def find_nearest_node(
        self,
        latitude,
        longitude
    ):
        """
        Find the closest road network node to a
        geographic location.
        """

        return ox.distance.nearest_nodes(
            self.graph,
            X=longitude,
            Y=latitude
        )


    def find_nearest_nodes(
        self,
        latitude,
        longitude,
        count=5
    ):
        """
        Find multiple nearby road-network nodes.

        This provides fallback routing options when the
        closest node cannot reach the destination due to
        one-way roads, disconnected components, or
        blocked disaster zones.

        Returns nearby nodes ordered from closest to
        farthest.
        """

        node_distances = []


        for node_id, node_data in (
            self.graph.nodes(data=True)
        ):

            node_latitude = node_data["y"]

            node_longitude = node_data["x"]


            # Squared geographic distance is sufficient
            # for ranking nearby nodes.
            distance = (

                (node_latitude - latitude) ** 2

                +

                (node_longitude - longitude) ** 2

            )


            node_distances.append(
                (
                    distance,
                    node_id
                )
            )


        node_distances.sort(
            key=lambda item: item[0]
        )


        return [

            node_id

            for _, node_id

            in node_distances[:count]

        ]


    def initialize_edge_attributes(self):
        """
        Add disaster-aware attributes to every road segment.
        """

        random.seed(42)


        for source, target, key, data in (
            self.graph.edges(
                keys=True,
                data=True
            )
        ):

            # Calculate estimated travel time
            travel_time = (
                self._calculate_travel_time(
                    data
                )
            )


            # Simulated traffic level between 0 and 1
            traffic_level = random.uniform(
                0.0,
                1.0
            )


            # Initial disaster state
            risk_level = 0.0

            blocked = False


            # Store attributes
            data["travel_time"] = travel_time

            data["traffic_level"] = traffic_level

            data["risk_level"] = risk_level

            data["blocked"] = blocked


    def calculate_dynamic_costs(
        self,
        cost_calculator=None
    ):
        """
        Calculate and assign a dynamic cost to every
        road segment.
        """

        if cost_calculator is not None:

            self.cost_calculator = (
                cost_calculator
            )


        if self.cost_calculator is None:

            raise ValueError(
                "A CostCalculator is required."
            )


        # Store maximum values for normalization
        self.max_distance = max(

            data.get("length", 0)

            for _, _, _, data

            in self.graph.edges(
                keys=True,
                data=True
            )

        )


        self.max_travel_time = max(

            data.get("travel_time", 0)

            for _, _, _, data

            in self.graph.edges(
                keys=True,
                data=True
            )

        )


        # Calculate dynamic cost for every road
        for source, target, key, data in (
            self.graph.edges(
                keys=True,
                data=True
            )
        ):

            self.recalculate_road_cost(
                source,
                target,
                key
            )


    def recalculate_road_cost(
        self,
        source,
        target,
        key=0
    ):
        """
        Recalculate the dynamic cost of a single
        road segment.
        """

        if self.cost_calculator is None:

            raise ValueError(
                "CostCalculator has not been initialized."
            )


        edge_data = self.graph[
            source
        ][
            target
        ][
            key
        ]


        normalized_distance = (
            self.cost_calculator.normalize(
                edge_data.get(
                    "length",
                    0
                ),
                self.max_distance
            )
        )


        normalized_time = (
            self.cost_calculator.normalize(
                edge_data.get(
                    "travel_time",
                    0
                ),
                self.max_travel_time
            )
        )


        dynamic_cost = (
            self.cost_calculator.calculate_cost(
                normalized_distance=(
                    normalized_distance
                ),
                normalized_time=(
                    normalized_time
                ),
                traffic_level=(
                    edge_data.get(
                        "traffic_level",
                        0
                    )
                ),
                risk_level=(
                    edge_data.get(
                        "risk_level",
                        0
                    )
                )
            )
        )


        edge_data[
            "dynamic_cost"
        ] = dynamic_cost


    def update_road_risk(
        self,
        source,
        target,
        key,
        risk_level
    ):
        """
        Update the risk level of a road and
        recalculate its cost.
        """

        if not 0.0 <= risk_level <= 1.0:

            raise ValueError(
                "Risk level must be between 0 and 1."
            )


        edge_data = self.graph[
            source
        ][
            target
        ][
            key
        ]


        edge_data[
            "risk_level"
        ] = risk_level


        self.recalculate_road_cost(
            source,
            target,
            key
        )


    def block_road(
        self,
        source,
        target,
        key=0
    ):
        """
        Mark a road as blocked.
        """

        edge_data = self.graph[
            source
        ][
            target
        ][
            key
        ]


        edge_data[
            "blocked"
        ] = True


    def unblock_road(
        self,
        source,
        target,
        key=0
    ):
        """
        Mark a road as available again.
        """

        edge_data = self.graph[
            source
        ][
            target
        ][
            key
        ]


        edge_data[
            "blocked"
        ] = False


    def _calculate_travel_time(
        self,
        edge_data
    ):
        """
        Calculate estimated travel time in seconds.
        """

        length = edge_data.get(
            "length",
            0
        )


        speed_kmh = self._get_speed(
            edge_data
        )


        # Convert km/h to m/s
        speed_mps = (
            speed_kmh * 1000 / 3600
        )


        if speed_mps == 0:

            return float("inf")


        return length / speed_mps


    def _get_speed(
        self,
        edge_data
    ):
        """
        Get road speed from OpenStreetMap data.

        Uses fallback speeds when maxspeed is unavailable.
        """

        maxspeed = edge_data.get(
            "maxspeed"
        )


        if maxspeed:

            return self._parse_speed(
                maxspeed
            )


        highway_type = edge_data.get(
            "highway",
            "residential"
        )


        fallback_speeds = {

            "motorway": 80,

            "trunk": 60,

            "primary": 50,

            "secondary": 40,

            "tertiary": 35,

            "residential": 30,

            "service": 20,

        }


        return fallback_speeds.get(
            highway_type,
            30
        )


    def _parse_speed(
        self,
        maxspeed
    ):
        """
        Convert OpenStreetMap maxspeed values into km/h.
        """

        # Handle list values
        if isinstance(
            maxspeed,
            list
        ):

            maxspeed = maxspeed[0]


        maxspeed = str(
            maxspeed
        )


        # Handle mph
        if "mph" in maxspeed.lower():

            speed = float(

                maxspeed.lower()
                .replace(
                    "mph",
                    ""
                )
                .strip()

            )


            return speed * 1.60934


        # Handle km/h
        try:

            return float(
                maxspeed
            )

        except ValueError:

            return 30


    def validate_edge_attributes(self):
        """
        Validate that all roads contain the required
        disaster-aware attributes.
        """

        required_attributes = [

            "travel_time",

            "traffic_level",

            "risk_level",

            "blocked",

            "dynamic_cost"

        ]


        missing_attributes = 0


        total_edges = (
            self.graph.number_of_edges()
        )


        for _, _, _, data in (
            self.graph.edges(
                keys=True,
                data=True
            )
        ):

            for attribute in required_attributes:

                if attribute not in data:

                    missing_attributes += 1


        return {

            "total_edges":
                total_edges,

            "missing_attributes":
                missing_attributes,

            "valid":
                missing_attributes == 0

        }