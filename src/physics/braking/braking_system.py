from ..interfaces.braking_strategy import IBrakingStrategy


class BrakingSystem(IBrakingStrategy):
    MIN_GAP = 0.1
    MIN_CRITICAL_TTC = 0.5
    DEFAULT_MAX_DECELERATION = 3.0
    DEFAULT_COMFORTABLE_DECELERATION = 2.0

    def __init__(
        self,
        min_gap=2.0,
        ttc_threshold=1.0,
        stop_distance=10.0,
        brake_on_yellow=True,
    ):
        self.min_gap = float(min_gap)
        self.ttc_threshold = float(ttc_threshold)
        self.stop_distance = float(stop_distance)
        self.brake_on_yellow = bool(brake_on_yellow)

    def should_brake(self, vehicle, environment):
        gap = self._lead_gap(environment)
        if self._should_brake_for_signal(environment):
            environment["braking_deceleration"] = self._signal_braking_deceleration(environment)
            return True

        if self._should_brake_for_lead(environment, gap):
            environment["braking_deceleration"] = self._lead_braking_deceleration(environment, gap)
            return True

        return False

    def braking_deceleration(self, vehicle, environment):
        if "braking_deceleration" in environment:
            return environment["braking_deceleration"]

        gap = self._lead_gap(environment)
        if self._should_brake_for_signal(environment):
            return self._signal_braking_deceleration(environment)

        if self._should_brake_for_lead(environment, gap):
            return self._lead_braking_deceleration(environment, gap)

        return -self.DEFAULT_COMFORTABLE_DECELERATION

    def _signal_braking_deceleration(self, environment):
        if not self._should_brake_for_signal(environment):
            return None

        distance = environment.get("distance_to_signal")
        if distance is None or distance <= 0:
            return -self.DEFAULT_MAX_DECELERATION

        velocity = max(0.0, environment.get("vehicle_velocity", 0.0))
        if velocity <= 0.0:
            return -self.DEFAULT_COMFORTABLE_DECELERATION

        required_deceleration = (velocity * velocity) / (2.0 * max(distance, self.MIN_GAP))
        braking_strength = max(self.DEFAULT_COMFORTABLE_DECELERATION, required_deceleration)
        return -braking_strength

    def _lead_braking_deceleration(self, environment, gap):
        ttc = self._time_to_collision(environment, gap)

        if gap is not None and gap <= self.min_gap:
            return -self.DEFAULT_MAX_DECELERATION

        critical_ttc = max(self.MIN_CRITICAL_TTC, self.ttc_threshold * 0.5)
        if ttc is not None and ttc <= critical_ttc:
            return -self.DEFAULT_MAX_DECELERATION

        return -self.DEFAULT_COMFORTABLE_DECELERATION

    def _should_brake_for_signal(self, environment):
        signal_state = environment.get("signal_state")
        if signal_state is None:
            return False

        if signal_state == "RED":
            return self._within_stop_distance(environment)

        if self.brake_on_yellow and signal_state == "YELLOW":
            return self._within_stop_distance(environment)

        return False

    def _within_stop_distance(self, environment):
        distance = environment.get("distance_to_signal")
        if distance is None:
            return False
        return distance <= self.stop_distance

    def _should_brake_for_lead(self, environment, gap):
        if gap is None:
            return False

        if gap <= self.min_gap:
            return True

        velocity = max(0.0, environment.get("vehicle_velocity", 0.0))
        lead_velocity = max(0.0, getattr(environment.get("lead"), "velocity", 0.0))
        closing_speed = max(0.0, velocity - lead_velocity)

        if closing_speed <= 0.0:
            return False

        time_to_collision = gap / closing_speed
        return time_to_collision <= self.ttc_threshold

    def _lead_gap(self, environment):
        lead = environment.get("lead")
        if lead is None:
            return None
        vehicle_position = environment.get("vehicle_position", 0.0)
        return max(self.MIN_GAP, getattr(lead, "position", 0.0) - vehicle_position)

    def _time_to_collision(self, environment, gap):
        if gap is None:
            return None

        lead = environment.get("lead")
        if lead is None:
            return None

        velocity = max(0.0, environment.get("vehicle_velocity", 0.0))
        lead_velocity = max(0.0, getattr(lead, "velocity", 0.0))
        closing_speed = max(0.0, velocity - lead_velocity)

        if closing_speed <= 0.0:
            return None

        return gap / closing_speed
