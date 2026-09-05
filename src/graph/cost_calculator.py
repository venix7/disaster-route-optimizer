class CostCalculator:
    def __init__(
        self,
        distance_weight=0.30,
        time_weight=0.25,
        traffic_weight=0.10,
        risk_weight=0.35
    ):
        """
        Initialize weights for evacuation route cost.

        Risk is given slightly higher priority than
        distance and travel time.
        """

        self.distance_weight = distance_weight
        self.time_weight = time_weight
        self.traffic_weight = traffic_weight
        self.risk_weight = risk_weight


    def calculate_cost(
        self,
        normalized_distance,
        normalized_time,
        traffic_level,
        risk_level
    ):
        """
        Calculate the dynamic evacuation cost
        of a road segment.
        """

        cost = (
            self.distance_weight * normalized_distance
            + self.time_weight * normalized_time
            + self.traffic_weight * traffic_level
            + self.risk_weight * risk_level
        )

        return cost


    @staticmethod
    def normalize(value, max_value):
        """
        Normalize a value to the range 0 to 1.
        """

        if max_value == 0:
            return 0.0

        return value / max_value