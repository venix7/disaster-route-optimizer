import math


class FloodSimulator:
    def __init__(self, road_network):
        self.road_network = road_network
        self.graph = road_network.graph

    @staticmethod
    def calculate_distance(
        lat1,
        lon1,
        lat2,
        lon2
    ):
        """
        Calculate distance between two geographic coordinates
        using the Haversine formula.

        Returns distance in meters.
        """

        earth_radius = 6371000

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)

        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        delta_lat = lat2_rad - lat1_rad
        delta_lon = lon2_rad - lon1_rad

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad)
            * math.cos(lat2_rad)
            * math.sin(delta_lon / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        return earth_radius * c

    def simulate_flood(
        self,
        center_latitude,
        center_longitude,
        affected_radius,
        severe_radius
    ):
        """
        Simulate a flood event.

        Roads inside the severe radius are blocked.

        Roads inside the affected radius receive a risk level
        based on their distance from the flood center.
        """

        affected_roads = 0
        blocked_roads = 0

        for source, target, key, edge_data in self.graph.edges(
            keys=True,
            data=True
        ):

            source_data = self.graph.nodes[source]
            target_data = self.graph.nodes[target]

            source_lat = source_data["y"]
            source_lon = source_data["x"]

            target_lat = target_data["y"]
            target_lon = target_data["x"]

            midpoint_lat = (
                source_lat + target_lat
            ) / 2

            midpoint_lon = (
                source_lon + target_lon
            ) / 2

            distance = self.calculate_distance(
                midpoint_lat,
                midpoint_lon,
                center_latitude,
                center_longitude
            )

            # Outside flood zone
            if distance > affected_radius:
                continue

            affected_roads += 1

            # Severe flooding
            if distance <= severe_radius:

                self.road_network.block_road(
                    source,
                    target,
                    key
                )

                blocked_roads += 1

            else:

                # Risk increases closer to flood center
                calculated_risk = (
                    1
                    - distance / affected_radius
                )

                calculated_risk = max(
                    0.1,
                    calculated_risk
                )

                # Preserve higher risk from previous events
                current_risk = edge_data.get(
                    "risk_level",
                    0.0
                )

                risk_level = max(
                    current_risk,
                    calculated_risk
                )

                self.road_network.update_road_risk(
                    source,
                    target,
                    key,
                    risk_level
                )

        return {
            "affected_roads": affected_roads,
            "blocked_roads": blocked_roads,
            "center": (
                center_latitude,
                center_longitude
            ),
            "affected_radius": affected_radius,
            "severe_radius": severe_radius
        }

    def reset_disaster(self):
        """
        Reset all disaster-related road conditions.
        """

        for source, target, key, edge_data in self.graph.edges(
            keys=True,
            data=True
        ):

            edge_data["risk_level"] = 0.0
            edge_data["blocked"] = False

            self.road_network.recalculate_road_cost(
                source,
                target,
                key
            )