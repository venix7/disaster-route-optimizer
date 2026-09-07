import math


class RouteAnalysisService:
    """
    Build deterministic facts that Groq can explain.

    This service never asks an LLM to calculate a route. It reads
    the exact edges selected by RouteEngine and applies the same
    cost weights used by RoadNetwork.
    """

    HIGH_RISK_THRESHOLD = 0.5

    def __init__(
        self,
        graph,
        road_network,
        route_engine
    ):

        self.graph = graph
        self.road_network = road_network
        self.route_engine = route_engine

    def analyze_route(
        self,
        route_result,
        hazard_status=None
    ):
        """
        Analyze a calculated route using its exact graph edges.
        """

        if route_result is None:

            return {
                "available": False,
                "reason": "No route result was supplied."
            }

        route_edges = route_result.get(
            "edges",
            []
        )

        route_metrics = route_result.get(
            "metrics",
            {}
        )

        edge_summary = self._analyze_edges(
            route_edges
        )

        total_dynamic_cost = self._number(
            route_result.get("total_cost")
        )

        cost_contributions = edge_summary[
            "cost_contributions"
        ]

        contribution_total = sum(
            cost_contributions.values()
        )

        if contribution_total > 0:

            contribution_percentages = {
                name: self._round(
                    value
                    / contribution_total
                    * 100
                )
                for name, value
                in cost_contributions.items()
            }

        else:

            contribution_percentages = {
                name: 0.0
                for name in cost_contributions
            }

        distance_comparison = (
            self._compare_with_distance_routes(
                route_result,
                hazard_status or {}
            )
        )

        analysis = {
            "available": True,
            "selection_method": (
                "custom Dijkstra minimizing total "
                "dynamic road cost"
            ),
            "cost_weights": self._get_cost_weights(),
            "cost_contributions": {
                name: self._round(value)
                for name, value
                in cost_contributions.items()
            },
            "cost_contribution_percentages": (
                contribution_percentages
            ),
            "calculated_contribution_total": (
                self._round(contribution_total)
            ),
            "reported_total_dynamic_cost": (
                self._round(total_dynamic_cost)
            ),
            "route_conditions": {
                "road_count": len(route_edges),
                "risky_road_count": edge_summary[
                    "risky_road_count"
                ],
                "high_risk_road_count": edge_summary[
                    "high_risk_road_count"
                ],
                "blocked_road_count": edge_summary[
                    "blocked_road_count"
                ],
                "average_traffic_level": self._round(
                    edge_summary[
                        "average_traffic_level"
                    ]
                ),
                "missing_edge_count": edge_summary[
                    "missing_edge_count"
                ]
            },
            "distance_comparison": distance_comparison,
            "hazard_snapshot": hazard_status or {
                "active": False,
                "affected_roads": 0,
                "blocked_roads": 0
            }
        }

        analysis["facts"] = self._build_route_facts(
            analysis,
            route_metrics
        )

        return analysis

    def analyze_shelter_recommendation(
        self,
        recommendation_result
    ):
        """
        Explain a shelter choice by comparing the routes that
        EvacuationService actually evaluated.
        """

        if not recommendation_result:

            return {
                "available": False,
                "reason": (
                    "No shelter recommendation was supplied."
                )
            }

        recommended_item = recommendation_result.get(
            "recommended_shelter"
        )

        evaluated_items = recommendation_result.get(
            "evaluated_shelters",
            []
        )

        recommended = self._shelter_summary(
            recommended_item
        )

        evaluated = [
            summary
            for item in evaluated_items
            if (
                summary := self._shelter_summary(
                    item
                )
            ) is not None
        ]

        if recommended is None:

            return {
                "available": False,
                "reason": (
                    "The recommendation does not contain "
                    "a valid shelter route."
                )
            }

        if not evaluated:

            evaluated = [recommended]

        ranked_by_cost = sorted(
            evaluated,
            key=lambda item: item[
                "total_dynamic_cost"
            ]
        )

        nearest = min(
            evaluated,
            key=lambda item: item[
                "total_distance"
            ]
        )

        lowest_risk = min(
            evaluated,
            key=lambda item: (
                item["average_risk"],
                item["maximum_risk"],
                item["total_dynamic_cost"]
            )
        )

        runner_up = next(
            (
                item
                for item in ranked_by_cost
                if item["id"] != recommended["id"]
            ),
            None
        )

        result = {
            "available": True,
            "selection_rule": (
                "lowest total dynamic route cost among "
                "reachable active shelters with remaining capacity"
            ),
            "capacity_used_as_eligibility_filter": True,
            "capacity_used_in_ranking": False,
            "reachable_shelters_evaluated": len(
                evaluated
            ),
            "recommended": recommended,
            "runner_up_by_dynamic_cost": runner_up,
            "nearest_by_route_distance": nearest,
            "lowest_average_risk": lowest_risk,
            "nearest_is_recommended": (
                nearest["id"] == recommended["id"]
            ),
            "lowest_risk_is_recommended": (
                lowest_risk["id"] == recommended["id"]
            )
        }

        if runner_up is not None:

            result[
                "dynamic_cost_margin_over_runner_up"
            ] = self._round(
                runner_up["total_dynamic_cost"]
                - recommended["total_dynamic_cost"]
            )

        else:

            result[
                "dynamic_cost_margin_over_runner_up"
            ] = None

        result["facts"] = (
            self._build_shelter_facts(
                result
            )
        )

        return result

    def _analyze_edges(
        self,
        route_edges
    ):

        contributions = {
            "distance": 0.0,
            "travel_time": 0.0,
            "traffic": 0.0,
            "risk": 0.0
        }

        traffic_total = 0.0
        resolved_edge_count = 0
        risky_road_count = 0
        high_risk_road_count = 0
        blocked_road_count = 0
        missing_edge_count = 0

        calculator = self.road_network.cost_calculator

        for edge in route_edges:

            if len(edge) != 3:

                missing_edge_count += 1
                continue

            source, target, key = edge

            edge_data = self.graph.get_edge_data(
                source,
                target,
                key
            )

            if edge_data is None:

                missing_edge_count += 1
                continue

            resolved_edge_count += 1

            distance = self._number(
                edge_data.get("length")
            )

            travel_time = self._number(
                edge_data.get("travel_time")
            )

            traffic_level = self._number(
                edge_data.get("traffic_level")
            )

            risk_level = self._number(
                edge_data.get("risk_level")
            )

            normalized_distance = calculator.normalize(
                distance,
                self.road_network.max_distance
            )

            normalized_time = calculator.normalize(
                travel_time,
                self.road_network.max_travel_time
            )

            contributions["distance"] += (
                calculator.distance_weight
                * normalized_distance
            )

            contributions["travel_time"] += (
                calculator.time_weight
                * normalized_time
            )

            contributions["traffic"] += (
                calculator.traffic_weight
                * traffic_level
            )

            contributions["risk"] += (
                calculator.risk_weight
                * risk_level
            )

            traffic_total += traffic_level

            if risk_level > 0:
                risky_road_count += 1

            if risk_level >= self.HIGH_RISK_THRESHOLD:
                high_risk_road_count += 1

            if edge_data.get("blocked", False):
                blocked_road_count += 1

        average_traffic_level = (
            traffic_total / resolved_edge_count
            if resolved_edge_count > 0
            else 0.0
        )

        return {
            "cost_contributions": contributions,
            "average_traffic_level": (
                average_traffic_level
            ),
            "risky_road_count": risky_road_count,
            "high_risk_road_count": (
                high_risk_road_count
            ),
            "blocked_road_count": blocked_road_count,
            "missing_edge_count": missing_edge_count
        }

    def _compare_with_distance_routes(
        self,
        route_result,
        hazard_status
    ):

        route_nodes = route_result.get(
            "nodes",
            []
        )

        if len(route_nodes) < 2:
            return None

        start_node = route_nodes[0]
        destination_node = route_nodes[-1]

        shortest_passable = self.route_engine.find_route(
            start_node,
            destination_node,
            cost_attribute="length"
        )

        if shortest_passable is None:
            return None

        selected_metrics = route_result.get(
            "metrics",
            {}
        )

        selected_distance = self._number(
            selected_metrics.get("total_distance")
        )

        shortest_distance = self._number(
            shortest_passable["metrics"].get(
                "total_distance"
            )
        )

        selected_dynamic_cost = self._number(
            route_result.get("total_cost")
        )

        shortest_dynamic_cost = (
            self._sum_dynamic_cost(
                shortest_passable.get(
                    "edges",
                    []
                )
            )
        )

        comparison = {
            "is_shortest_passable_route": math.isclose(
                selected_distance,
                shortest_distance,
                abs_tol=0.5
            ),
            "selected_distance": self._round(
                selected_distance
            ),
            "shortest_passable_distance": self._round(
                shortest_distance
            ),
            "additional_distance_vs_shortest_passable": (
                self._round(
                    max(
                        0.0,
                        selected_distance
                        - shortest_distance
                    )
                )
            ),
            "selected_dynamic_cost": self._round(
                selected_dynamic_cost
            ),
            "shortest_passable_dynamic_cost": self._round(
                shortest_dynamic_cost
            ),
            "dynamic_cost_saved_vs_shortest_passable": (
                self._round(
                    shortest_dynamic_cost
                    - selected_dynamic_cost
                )
            ),
            "shortest_passable_average_risk": (
                self._round(
                    self._number(
                        shortest_passable[
                            "metrics"
                        ].get("average_risk")
                    )
                )
            ),
            "shortest_passable_maximum_risk": (
                self._round(
                    self._number(
                        shortest_passable[
                            "metrics"
                        ].get("maximum_risk")
                    )
                )
            ),
            "flood_forced_detour": False,
            "shortest_without_closures": None
        }

        if hazard_status.get("blocked_roads", 0) > 0:

            unrestricted_shortest = (
                self.route_engine.find_route(
                    start_node,
                    destination_node,
                    cost_attribute="length",
                    allow_blocked=True
                )
            )

            if unrestricted_shortest is not None:

                unrestricted_conditions = (
                    self._analyze_edges(
                        unrestricted_shortest.get(
                            "edges",
                            []
                        )
                    )
                )

                unrestricted_distance = self._number(
                    unrestricted_shortest[
                        "metrics"
                    ].get("total_distance")
                )

                blocked_count = unrestricted_conditions[
                    "blocked_road_count"
                ]

                comparison[
                    "shortest_without_closures"
                ] = {
                    "total_distance": self._round(
                        unrestricted_distance
                    ),
                    "blocked_road_count": blocked_count
                }

                comparison["flood_forced_detour"] = (
                    blocked_count > 0
                    and selected_distance
                    > unrestricted_distance + 0.5
                )

        return comparison

    def _sum_dynamic_cost(
        self,
        route_edges
    ):

        total = 0.0

        for source, target, key in route_edges:

            edge_data = self.graph.get_edge_data(
                source,
                target,
                key
            )

            if edge_data is not None:

                total += self._number(
                    edge_data.get("dynamic_cost")
                )

        return total

    def _get_cost_weights(self):

        calculator = self.road_network.cost_calculator

        return {
            "distance": calculator.distance_weight,
            "travel_time": calculator.time_weight,
            "traffic": calculator.traffic_weight,
            "risk": calculator.risk_weight
        }

    def _build_route_facts(
        self,
        analysis,
        route_metrics
    ):

        weights = analysis["cost_weights"]

        facts = [
            (
                "The route was selected by the custom "
                "Dijkstra engine using total dynamic cost, "
                "not distance alone."
            ),
            (
                "The configured weights are "
                f"risk {weights['risk']:.0%}, "
                f"distance {weights['distance']:.0%}, "
                f"travel time {weights['travel_time']:.0%}, "
                f"and traffic {weights['traffic']:.0%}."
            ),
            (
                "The selected route is "
                f"{self._number(route_metrics.get('total_distance')):.1f} "
                "meters with an average risk of "
                f"{self._number(route_metrics.get('average_risk')):.3f} "
                "and a maximum risk of "
                f"{self._number(route_metrics.get('maximum_risk')):.3f}."
            )
        ]

        route_conditions = analysis[
            "route_conditions"
        ]

        if route_conditions["blocked_road_count"] == 0:

            facts.append(
                "No blocked road is included in the selected route."
            )

        comparison = analysis.get(
            "distance_comparison"
        )

        if comparison is not None:

            if comparison[
                "is_shortest_passable_route"
            ]:

                facts.append(
                    "The selected route is also the shortest "
                    "currently passable route between its "
                    "snapped road-network endpoints."
                )

            else:

                facts.append(
                    "The selected route is "
                    f"{comparison['additional_distance_vs_shortest_passable']:.1f} "
                    "meters longer than the shortest passable "
                    "route between the same snapped endpoints."
                )

            if comparison["flood_forced_detour"]:

                facts.append(
                    "The distance-only route without closures "
                    "contains blocked roads, so the flood forced "
                    "a passable detour."
                )

        hazard = analysis.get(
            "hazard_snapshot",
            {}
        )

        if hazard.get("active"):

            facts.append(
                "At calculation time the flood affected "
                f"{hazard.get('affected_roads', 0)} roads and "
                f"blocked {hazard.get('blocked_roads', 0)} roads."
            )

        return facts

    def _shelter_summary(
        self,
        shelter_item
    ):

        if not shelter_item:
            return None

        shelter = shelter_item.get(
            "shelter",
            {}
        )

        route = shelter_item.get(
            "route",
            {}
        )

        metrics = route.get(
            "metrics",
            {}
        )

        if "total_cost" not in route:
            return None

        return {
            "id": shelter.get("id"),
            "name": shelter.get("name"),
            "available_capacity": shelter.get(
                "available_capacity"
            ),
            "total_dynamic_cost": self._round(
                self._number(
                    route.get("total_cost")
                )
            ),
            "total_distance": self._round(
                self._number(
                    metrics.get("total_distance")
                )
            ),
            "total_travel_time": self._round(
                self._number(
                    metrics.get("total_travel_time")
                )
            ),
            "average_risk": self._round(
                self._number(
                    metrics.get("average_risk")
                )
            ),
            "maximum_risk": self._round(
                self._number(
                    metrics.get("maximum_risk")
                )
            )
        }

    def _build_shelter_facts(
        self,
        analysis
    ):

        recommended = analysis["recommended"]

        facts = [
            (
                f"{recommended['name']} was selected because "
                "its reachable route had the lowest total "
                "dynamic cost among active shelters with "
                "remaining capacity."
            ),
            (
                "Remaining capacity is an eligibility check, but "
                "capacity size is not part of the route-cost ranking "
                "formula."
            )
        ]

        runner_up = analysis.get(
            "runner_up_by_dynamic_cost"
        )

        if runner_up is not None:

            facts.append(
                "Its dynamic-cost margin over the runner-up "
                f"({runner_up['name']}) was "
                f"{analysis['dynamic_cost_margin_over_runner_up']:.4f}."
            )

        nearest = analysis[
            "nearest_by_route_distance"
        ]

        if analysis["nearest_is_recommended"]:

            facts.append(
                "The recommended shelter was also the nearest "
                "by passable route distance."
            )

        else:

            facts.append(
                f"The nearest shelter by route distance was "
                f"{nearest['name']}; nearest distance alone did "
                "not determine the recommendation."
            )

        return facts

    @staticmethod
    def _number(
        value,
        default=0.0
    ):

        try:
            number = float(value)
        except (TypeError, ValueError):
            return default

        if not math.isfinite(number):
            return default

        return number

    @staticmethod
    def _round(value):

        return round(
            float(value),
            6
        )
