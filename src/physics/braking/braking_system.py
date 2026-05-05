"""Unified braking system combining emergency and signal-aware logic."""

from ..interfaces.braking_strategy import IBrakingStrategy


class BrakingSystem(IBrakingStrategy):
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
        gap = self._lead_gap(vehicle, environment)
        if self._should_brake_for_signal(environment):
            return True

        return self._should_brake_for_lead(vehicle, environment, gap)

    def braking_deceleration(self, vehicle, environment):
        gap = self._lead_gap(vehicle, environment)
        ttc = self._time_to_collision(vehicle, environment, gap)

        max_acceleration = abs(getattr(vehicle.physics_model, "max_acceleration", 3.0))
        comfortable_braking = abs(getattr(vehicle.physics_model, "comfortable_braking", 2.0))

        signal_braking = self._signal_braking_deceleration(vehicle, environment, comfortable_braking, max_acceleration)
        if signal_braking is not None:
            return signal_braking

        if gap is not None and gap <= self.min_gap:
            return -max_acceleration

        critical_ttc = max(0.5, self.ttc_threshold * 0.5)
        if ttc is not None and ttc <= critical_ttc:
            return -max_acceleration

        return -comfortable_braking

    def _signal_braking_deceleration(self, vehicle, environment, comfortable_braking, max_acceleration):
        if not self._should_brake_for_signal(environment):
            return None

        distance = environment.get("distance_to_signal")
        if distance is None or distance <= 0:
            return -max_acceleration

        velocity = max(0.0, getattr(vehicle, "velocity", 0.0))
        if velocity <= 0.0:
            return -comfortable_braking

        required_deceleration = (velocity * velocity) / (2.0 * max(distance, 0.1))
        braking_strength = max(comfortable_braking, required_deceleration)
        return -braking_strength

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

    def _should_brake_for_lead(self, vehicle, environment, gap):
        if gap is None:
            return False

        if gap <= self.min_gap:
            return True

        velocity = max(0.0, getattr(vehicle, "velocity", 0.0))
        lead_velocity = max(0.0, getattr(environment.get("lead"), "velocity", 0.0))
        closing_speed = max(0.0, velocity - lead_velocity)

        if closing_speed <= 0.0:
            return False

        time_to_collision = gap / closing_speed
        return time_to_collision <= self.ttc_threshold

    def _lead_gap(self, vehicle, environment):
        lead = environment.get("lead")
        if lead is None:
            return None
        return max(0.1, getattr(lead, "position", 0.0) - getattr(vehicle, "position", 0.0))

    def _time_to_collision(self, vehicle, environment, gap):
        if gap is None:
            return None

        lead = environment.get("lead")
        if lead is None:
            return None

        velocity = max(0.0, getattr(vehicle, "velocity", 0.0))
        lead_velocity = max(0.0, getattr(lead, "velocity", 0.0))
        closing_speed = max(0.0, velocity - lead_velocity)

        if closing_speed <= 0.0:
            return None

        return gap / closing_speed
