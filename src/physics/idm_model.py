"""Intelligent Driver Model implementation."""

from math import sqrt

from .interfaces.physics_model import IPhysicsModel


class IDMModel(IPhysicsModel):
    def __init__(self):
        self.desired_velocity = 30.0  # m/s
        self.max_acceleration = 3.0  # m/s^2
        self.comfortable_braking = 2.0  # m/s^2
        self.comfortable_breaking = self.comfortable_braking  # compatibility alias
        self.minimum_distance = 2.0  # m
        self.time_headway = 1.5  # s
        self.delta = 4.0  # acceleration exponent

    def _free_road_term(self, velocity):
        if self.desired_velocity <= 0:
            return 0.0
        return 1 - (velocity / self.desired_velocity) ** self.delta

    def _desired_gap(self, velocity, relative_speed):
        braking_term = 0.0
        if relative_speed > 0:
            braking_term = (velocity * relative_speed) / (
                2 * sqrt(self.max_acceleration * self.comfortable_braking)
            )

        return self.minimum_distance + max(
            0.0,
            velocity * self.time_headway + braking_term,
        )

    def compute_acceleration(self, vehicle, lead):
        velocity = max(0.0, getattr(vehicle, "velocity", 0.0))
        free_term = self._free_road_term(velocity)

        if lead is None:
            return self._clamp_acceleration(self.max_acceleration * free_term)

        lead_position = getattr(lead, "position", vehicle.position)
        lead_velocity = getattr(lead, "velocity", 0.0)

        gap = max(0.1, lead_position - vehicle.position)
        relative_speed = velocity - lead_velocity
        desired_gap = self._desired_gap(velocity, relative_speed)
        interaction_term = (desired_gap / gap) ** 2

        acc = self.max_acceleration * (free_term - interaction_term)
        return self._clamp_acceleration(acc)

    def _clamp_acceleration(self, acceleration):
        if acceleration > self.max_acceleration:
            return self.max_acceleration
        if acceleration < -self.comfortable_braking:
            return -self.comfortable_braking
        return acceleration
