import json

from langchain.tools import tool


class AssistantToolbox:
    """
    LangChain tools backed by the existing deterministic services.

    The tools intentionally accept no coordinates from Groq. Route
    commands use locations that the user already selected on the map,
    which prevents the model from inventing or guessing coordinates.
    """

    def __init__(
        self,
        evacuation_service,
        context
    ):

        self.evacuation_service = (
            evacuation_service
        )

        self.context = context or {}

        self.current_route = self.context.get(
            "route"
        )

        self.current_recommendation = (
            self.context.get(
                "shelter_recommendation"
            )
        )

        self.actions = []

    def build_tools(self):
        """
        Create request-scoped tools and their captured context.
        """

        @tool
        def find_route() -> str:
            """
            Calculate a real evacuation route between the start and
            destination currently selected on the dashboard map.
            Use this for route commands. If either selection is
            missing, ask the user to select it on the map.
            """

            start = self.context.get(
                "start_location"
            )

            destination = self.context.get(
                "destination_location"
            )

            if not start or not destination:

                return self._json({
                    "ok": False,
                    "error": (
                        "A start location and destination must "
                        "both be selected on the map first."
                    )
                })

            try:

                route_result = (
                    self.evacuation_service.find_route(
                        start_latitude=start[
                            "latitude"
                        ],
                        start_longitude=start[
                            "longitude"
                        ],
                        destination_latitude=destination[
                            "latitude"
                        ],
                        destination_longitude=destination[
                            "longitude"
                        ]
                    )
                )

                if route_result is None:

                    return self._json({
                        "ok": False,
                        "error": (
                            "No passable evacuation route was "
                            "found for the selected locations."
                        )
                    })

                self.evacuation_service.save_route_history(
                    start_latitude=start[
                        "latitude"
                    ],
                    start_longitude=start[
                        "longitude"
                    ],
                    destination_latitude=destination[
                        "latitude"
                    ],
                    destination_longitude=destination[
                        "longitude"
                    ],
                    route_result=route_result
                )

            except Exception:

                return self._json({
                    "ok": False,
                    "error": (
                        "The routing service could not complete "
                        "the request."
                    )
                })

            self.current_route = route_result
            self.current_recommendation = None

            self.actions.append({
                "type": "route_calculated",
                "payload": route_result
            })

            return self._json({
                "ok": True,
                "route": self._compact_route(
                    route_result
                )
            })

        @tool
        def find_best_shelter() -> str:
            """
            Run the existing shelter recommendation service from the
            start location currently selected on the dashboard map.
            The service evaluates real passable routes and selects the
            lowest dynamic-cost reachable shelter.
            """

            start = self.context.get(
                "start_location"
            )

            if not start:

                return self._json({
                    "ok": False,
                    "error": (
                        "A start location must be selected on "
                        "the map first."
                    )
                })

            try:

                recommendation = (
                    self.evacuation_service
                    .find_best_shelter(
                        start["latitude"],
                        start["longitude"]
                    )
                )

            except Exception:

                return self._json({
                    "ok": False,
                    "error": (
                        "The shelter service could not complete "
                        "the request."
                    )
                })

            if recommendation is None:

                return self._json({
                    "ok": False,
                    "error": (
                        "No reachable active shelter was found."
                    )
                })

            self.current_recommendation = (
                recommendation
            )

            self.current_route = recommendation[
                "recommended_shelter"
            ]["route"]

            self.actions.append({
                "type": "shelter_recommended",
                "payload": recommendation
            })

            return self._json({
                "ok": True,
                "recommendation": (
                    self._compact_recommendation(
                        recommendation
                    )
                )
            })

        @tool
        def get_hazards() -> str:
            """
            Read the current flood parameters and affected, risky, and
            blocked road counts from the live backend road network.
            Use this for every factual hazard or disaster-state query.
            """

            return self._json({
                "ok": True,
                "hazard_status": (
                    self.evacuation_service
                    .get_hazard_status()
                )
            })

        @tool
        def explain_route() -> str:
            """
            Return deterministic analysis for the exact route currently
            displayed, including metrics, weighted cost contributions,
            risk, blocked-road checks, flood state, and comparison with
            the shortest passable route. Use before explaining a route.
            """

            if not self.current_route:

                return self._json({
                    "ok": False,
                    "error": (
                        "There is no route currently displayed."
                    )
                })

            analysis = self.current_route.get(
                "analysis"
            )

            if analysis is None:

                analysis = (
                    self.evacuation_service
                    .route_analysis_service
                    .analyze_route(
                        self.current_route,
                        self.evacuation_service
                        .get_hazard_status()
                    )
                )

            current_hazard_status = (
                self.evacuation_service
                .get_hazard_status()
            )

            snapshot_version = analysis.get(
                "hazard_snapshot",
                {}
            ).get("state_version")

            current_version = current_hazard_status.get(
                "state_version"
            )

            state_changed = (
                snapshot_version is not None
                and current_version is not None
                and snapshot_version != current_version
            )

            return self._json({
                "ok": True,
                "route_metrics": self.current_route.get(
                    "metrics",
                    {}
                ),
                "route_analysis": analysis,
                "current_hazard_status": (
                    current_hazard_status
                ),
                "hazard_state_changed_since_route": (
                    state_changed
                )
            })

        @tool
        def explain_shelter() -> str:
            """
            Return deterministic comparison data for the current shelter
            recommendation: all evaluated shelters, route cost, distance,
            time, risk, runner-up, nearest shelter, and ranking rule.
            Use before explaining why a shelter was recommended.
            """

            if not self.current_recommendation:

                return self._json({
                    "ok": False,
                    "error": (
                        "There is no current shelter recommendation."
                    )
                })

            analysis = self.current_recommendation.get(
                "analysis"
            )

            if analysis is None:

                analysis = (
                    self.evacuation_service
                    .route_analysis_service
                    .analyze_shelter_recommendation(
                        self.current_recommendation
                    )
                )

            return self._json({
                "ok": True,
                "shelter_analysis": analysis
            })

        return [
            find_route,
            find_best_shelter,
            get_hazards,
            explain_route,
            explain_shelter
        ]

    @staticmethod
    def _compact_route(route_result):

        nodes = route_result.get(
            "nodes",
            []
        )

        return {
            "start_node": (
                nodes[0]
                if nodes
                else None
            ),
            "destination_node": (
                nodes[-1]
                if nodes
                else None
            ),
            "total_dynamic_cost": route_result.get(
                "total_cost"
            ),
            "metrics": route_result.get(
                "metrics",
                {}
            ),
            "analysis": route_result.get(
                "analysis"
            )
        }

    def _compact_recommendation(
        self,
        recommendation
    ):

        evaluated = []

        for item in recommendation.get(
            "evaluated_shelters",
            []
        ):

            shelter = item.get(
                "shelter",
                {}
            )

            route = item.get(
                "route",
                {}
            )

            evaluated.append({
                "shelter": {
                    "id": shelter.get("id"),
                    "name": shelter.get("name"),
                    "available_capacity": shelter.get(
                        "available_capacity"
                    )
                },
                "route": {
                    "total_dynamic_cost": route.get(
                        "total_cost"
                    ),
                    "metrics": route.get(
                        "metrics",
                        {}
                    )
                }
            })

        return {
            "analysis": recommendation.get(
                "analysis"
            ),
            "evaluated_shelters": evaluated
        }

    @staticmethod
    def _json(value):

        return json.dumps(
            value,
            default=str,
            separators=(",", ":")
        )
