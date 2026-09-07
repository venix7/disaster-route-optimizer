import unittest

from api.schemas import AssistantChatRequest
from disaster.flood_simulator import FloodSimulator
from graph.cost_calculator import CostCalculator
from routing.route_engine import RouteEngine
from services.route_analysis_service import (
    RouteAnalysisService
)


class MiniGraph:
    """Small MultiDiGraph-compatible fixture for deterministic tests."""

    def __init__(self):

        self.nodes = {
            1: {"x": 0.0000, "y": 0.0000},
            2: {"x": 0.0000, "y": 0.0004},
            3: {"x": 0.0000, "y": 0.0008}
        }

        self.adjacency = {
            1: {
                2: {0: {}},
                3: {0: {}}
            },
            2: {
                3: {0: {}}
            },
            3: {}
        }

    def add_edge_data(
        self,
        source,
        target,
        key,
        data
    ):

        self.adjacency[
            source
        ][
            target
        ][
            key
        ] = data

    def successors(self, node):

        return self.adjacency[
            node
        ].keys()

    def get_edge_data(
        self,
        source,
        target,
        key=None
    ):

        edge_dictionary = self.adjacency.get(
            source,
            {}
        ).get(target)

        if key is None:
            return edge_dictionary

        if edge_dictionary is None:
            return None

        return edge_dictionary.get(key)

    def edges(
        self,
        keys=False,
        data=False
    ):

        result = []

        for source, targets in self.adjacency.items():
            for target, keyed_edges in targets.items():
                for key, edge_data in keyed_edges.items():
                    result.append(
                        (
                            source,
                            target,
                            key,
                            edge_data
                        )
                    )

        return result

    def __getitem__(self, node):

        return self.adjacency[node]


class MiniRoadNetwork:

    def __init__(self, graph):

        self.graph = graph
        self.cost_calculator = CostCalculator()
        self.max_distance = 120.0
        self.max_travel_time = 12.0

    def set_edge(
        self,
        source,
        target,
        length,
        travel_time,
        traffic,
        risk=0.0
    ):

        edge_data = {
            "length": length,
            "travel_time": travel_time,
            "traffic_level": traffic,
            "risk_level": risk,
            "blocked": False
        }

        self.graph.add_edge_data(
            source,
            target,
            0,
            edge_data
        )

        self.recalculate_road_cost(
            source,
            target,
            0
        )

    def recalculate_road_cost(
        self,
        source,
        target,
        key
    ):

        edge_data = self.graph[
            source
        ][
            target
        ][
            key
        ]

        edge_data["dynamic_cost"] = (
            self.cost_calculator.calculate_cost(
                normalized_distance=(
                    self.cost_calculator.normalize(
                        edge_data["length"],
                        self.max_distance
                    )
                ),
                normalized_time=(
                    self.cost_calculator.normalize(
                        edge_data["travel_time"],
                        self.max_travel_time
                    )
                ),
                traffic_level=edge_data[
                    "traffic_level"
                ],
                risk_level=edge_data[
                    "risk_level"
                ]
            )
        )

    def block_road(
        self,
        source,
        target,
        key
    ):

        self.graph[
            source
        ][
            target
        ][
            key
        ]["blocked"] = True

    def update_road_risk(
        self,
        source,
        target,
        key,
        risk_level
    ):

        self.graph[
            source
        ][
            target
        ][
            key
        ]["risk_level"] = risk_level

        self.recalculate_road_cost(
            source,
            target,
            key
        )


class Phase8Tests(unittest.TestCase):

    def setUp(self):

        self.graph = MiniGraph()
        self.road_network = MiniRoadNetwork(
            self.graph
        )

        # The two-edge path is shorter but much riskier.
        self.road_network.set_edge(
            1,
            2,
            length=50.0,
            travel_time=5.0,
            traffic=0.9,
            risk=0.9
        )

        self.road_network.set_edge(
            2,
            3,
            length=50.0,
            travel_time=5.0,
            traffic=0.9,
            risk=0.9
        )

        # The direct path is longer but has a lower dynamic cost.
        self.road_network.set_edge(
            1,
            3,
            length=120.0,
            travel_time=12.0,
            traffic=0.1,
            risk=0.0
        )

        self.route_engine = RouteEngine(
            self.graph,
            self.road_network
        )

    def test_dynamic_route_is_not_forced_to_be_shortest(self):

        selected = self.route_engine.find_route(
            1,
            3
        )

        shortest = self.route_engine.find_route(
            1,
            3,
            cost_attribute="length"
        )

        self.assertEqual(
            selected["edges"],
            [(1, 3, 0)]
        )

        self.assertEqual(
            shortest["edges"],
            [(1, 2, 0), (2, 3, 0)]
        )

    def test_route_analysis_uses_actual_cost_factors(self):

        route = self.route_engine.find_route(
            1,
            3
        )

        analyzer = RouteAnalysisService(
            self.graph,
            self.road_network,
            self.route_engine
        )

        analysis = analyzer.analyze_route(
            route,
            {
                "active": False,
                "affected_roads": 0,
                "blocked_roads": 0,
                "state_version": 0
            }
        )

        comparison = analysis[
            "distance_comparison"
        ]

        self.assertFalse(
            comparison[
                "is_shortest_passable_route"
            ]
        )

        self.assertEqual(
            comparison[
                "additional_distance_vs_shortest_passable"
            ],
            20.0
        )

        self.assertGreater(
            comparison[
                "dynamic_cost_saved_vs_shortest_passable"
            ],
            0
        )

        self.assertEqual(
            analysis[
                "route_conditions"
            ]["blocked_road_count"],
            0
        )

    def test_flood_status_is_versioned_and_resettable(self):

        simulator = FloodSimulator(
            self.road_network
        )

        result = simulator.simulate_flood(
            center_latitude=0.0,
            center_longitude=0.0,
            affected_radius=500.0,
            severe_radius=10.0
        )

        active_status = (
            simulator.get_hazard_status()
        )

        self.assertTrue(
            active_status["active"]
        )

        self.assertEqual(
            result["state_version"],
            1
        )

        self.assertGreater(
            active_status["blocked_roads"],
            0
        )

        simulator.reset_disaster()

        reset_status = (
            simulator.get_hazard_status()
        )

        self.assertFalse(
            reset_status["active"]
        )

        self.assertEqual(
            reset_status["blocked_roads"],
            0
        )

        self.assertEqual(
            reset_status["state_version"],
            2
        )

    def test_shelter_analysis_compares_actual_candidates(self):

        analyzer = RouteAnalysisService(
            self.graph,
            self.road_network,
            self.route_engine
        )

        recommended_route = self.route_engine.find_route(
            1,
            3
        )

        nearer_route = self.route_engine.find_route(
            1,
            3,
            cost_attribute="length"
        )

        nearer_route["total_cost"] = sum(
            self.graph.get_edge_data(
                source,
                target,
                key
            )["dynamic_cost"]
            for source, target, key
            in nearer_route["edges"]
        )

        recommendation = {
            "recommended_shelter": {
                "shelter": {
                    "id": 1,
                    "name": "Lower Cost Shelter",
                    "available_capacity": 100
                },
                "route": recommended_route
            },
            "evaluated_shelters": [
                {
                    "shelter": {
                        "id": 1,
                        "name": "Lower Cost Shelter",
                        "available_capacity": 100
                    },
                    "route": recommended_route
                },
                {
                    "shelter": {
                        "id": 2,
                        "name": "Nearer Shelter",
                        "available_capacity": 200
                    },
                    "route": nearer_route
                }
            ]
        }

        analysis = (
            analyzer.analyze_shelter_recommendation(
                recommendation
            )
        )

        self.assertFalse(
            analysis["nearest_is_recommended"]
        )

        self.assertTrue(
            analysis[
                "capacity_used_as_eligibility_filter"
            ]
        )

        self.assertFalse(
            analysis["capacity_used_in_ranking"]
        )

    def test_assistant_request_validates_nested_context(self):

        request = AssistantChatRequest.model_validate({
            "message": (
                "Why was this route selected?"
            ),
            "context": {
                "route": {
                    "nodes": [1, 3],
                    "edges": [[1, 3, 0]],
                    "total_cost": 0.56,
                    "metrics": {
                        "total_distance": 120.0,
                        "total_travel_time": 12.0,
                        "average_risk": 0.0,
                        "maximum_risk": 0.0,
                        "road_count": 1
                    }
                },
                "flood": {
                    "active": False
                }
            }
        })

        self.assertEqual(
            request.context.route.edges,
            [(1, 3, 0)]
        )


if __name__ == "__main__":
    unittest.main()
