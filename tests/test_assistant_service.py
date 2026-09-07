import unittest
from types import SimpleNamespace


try:
    from langchain.messages import AIMessage

    from llm.assistant_service import (
        AssistantService
    )

    LANGCHAIN_AVAILABLE = True

except ModuleNotFoundError:
    LANGCHAIN_AVAILABLE = False


class FakeEvacuationService:

    def __init__(self):
        self.saved_route = None

    def get_hazard_status(self):

        return {
            "active": False,
            "affected_roads": 0,
            "blocked_roads": 0,
            "state_version": 0
        }

    def find_route(self, **coordinates):

        return build_route()

    def save_route_history(self, **route_data):

        self.saved_route = route_data


class FakeModel:

    def __init__(self, responses):
        self.responses = list(responses)

    def bind_tools(self, assistant_tools):
        self.assistant_tools = assistant_tools
        return self

    def invoke(self, messages):
        return self.responses.pop(0)


def build_route():

    return {
        "nodes": [1, 2],
        "coordinates": [
            {"latitude": 40.73, "longitude": -74.00},
            {"latitude": 40.74, "longitude": -73.99}
        ],
        "edges": [(1, 2, 0)],
        "total_cost": 0.25,
        "metrics": {
            "total_distance": 100.0,
            "total_travel_time": 12.0,
            "average_risk": 0.1,
            "maximum_risk": 0.1,
            "road_count": 1
        },
        "analysis": {
            "hazard_snapshot": {
                "active": False,
                "state_version": 0
            },
            "facts": [
                "Verified route fact."
            ]
        }
    }


@unittest.skipUnless(
    LANGCHAIN_AVAILABLE,
    "LangChain dependencies are not installed."
)
class AssistantServiceTests(unittest.TestCase):

    def build_service(self, responses):

        return AssistantService(
            FakeEvacuationService(),
            settings=SimpleNamespace(
                is_configured=True,
                max_tool_rounds=4
            ),
            model=FakeModel(responses)
        )

    def test_route_explanation_requires_tool_grounding(self):

        service = self.build_service([
            AIMessage(
                content=(
                    "This first answer is intentionally "
                    "ungrounded."
                )
            ),
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "explain_route",
                    "args": {},
                    "id": "route-analysis-call",
                    "type": "tool_call"
                }]
            ),
            AIMessage(
                content=(
                    "The weighted dynamic cost selected "
                    "this route."
                )
            )
        ])

        result = service.chat(
            "Why was this route selected?",
            context={
                "route": build_route(),
                "flood": {"active": False}
            }
        )

        self.assertEqual(
            result["tools_used"],
            ["explain_route"]
        )

        self.assertNotIn(
            "intentionally ungrounded",
            result["reply"]
        )

    def test_route_tool_returns_a_frontend_action(self):

        service = self.build_service([
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "find_route",
                    "args": {},
                    "id": "find-route-call",
                    "type": "tool_call"
                }]
            ),
            AIMessage(
                content="I calculated the route using the backend."
            )
        ])

        result = service.chat(
            "Find a route for my selected locations.",
            context={
                "start_location": {
                    "latitude": 40.73,
                    "longitude": -74.00
                },
                "destination_location": {
                    "latitude": 40.74,
                    "longitude": -73.99
                },
                "flood": {"active": False}
            }
        )

        self.assertEqual(
            result["tools_used"],
            ["find_route"]
        )

        self.assertEqual(
            result["actions"][0]["type"],
            "route_calculated"
        )


if __name__ == "__main__":
    unittest.main()
