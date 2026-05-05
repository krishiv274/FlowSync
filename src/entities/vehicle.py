class Vehicle:
    MIN_VELOCITY = 0.0
    MIN_ACCELERATION = -10.0
    MAX_ACCELERATION = 5.0
    DEFAULT_BRAKING_DECELERATION = -2.0

    def __init__(self, position, velocity, physics_model=None, acceleration=0, braking_strategy=None):
        if isinstance(physics_model, (int, float)):
            acceleration = physics_model
            physics_model = None
        elif physics_model is not None and not hasattr(physics_model, "compute_acceleration"):
            physics_model = None

        self.position = float(position)
        self.velocity = max(self.MIN_VELOCITY, float(velocity))
        self.acceleration = self._clamp_acceleration(float(acceleration))
        self.physics_model = physics_model
        self.braking_strategy = braking_strategy
        self.signal_state = None
        self.render_direction: str | None = None
        self.lane: object | None = None

    def update(self, dt, lead_vehicle=None, distance_to_signal=None, **kwargs):
        if lead_vehicle is None and "lead" in kwargs:
            lead_vehicle = kwargs["lead"]

        if distance_to_signal is None:
            distance_to_signal = self._distance_to_signal_from_lane()

        previous_position = self.position
        environment = self._build_environment(lead_vehicle, distance_to_signal)

        # Braking is selected before normal physics, then motion is applied once.
        if self.braking_strategy and self.braking_strategy.should_brake(self, environment):
            acceleration = self._braking_deceleration(environment)
        else:
            acceleration = self._physics_acceleration(lead_vehicle)

        self.acceleration = self._clamp_acceleration(acceleration)
        self.velocity = max(self.MIN_VELOCITY, self.velocity + self.acceleration * dt)

        self.position += self.velocity * dt

        if self.signal_state == "RED" and distance_to_signal is not None:
            signal_position = previous_position + distance_to_signal
            if self.position >= signal_position:
                self.position = min(self.position, signal_position - 1e-6)
                self.velocity = 0

    def _distance_to_signal_from_lane(self):
        lane = getattr(self, "lane", None)
        if lane is None:
            return None

        intersection = getattr(lane, "intersection", None)
        if intersection is None:
            return None

        signal = intersection.get_signal_for_lane(lane)
        if signal is None:
            return None

        signal_pos = getattr(signal, "position", None)
        if not isinstance(signal_pos, tuple) or not signal_pos:
            return None

        vehicle_pos = getattr(self, "position", 0.0)
        signal_x = signal_pos[0]
        if vehicle_pos >= signal_x:
            return None

        return signal_x - vehicle_pos

    def on_signal_change(self, state):
        self.signal_state = state

    def _build_environment(self, lead_vehicle, distance_to_signal):
        return {
            "lead": lead_vehicle,
            "vehicle_position": self.position,
            "vehicle_velocity": self.velocity,
            "signal_state": self.signal_state,
            "distance_to_signal": distance_to_signal,
            "braking_deceleration": self.DEFAULT_BRAKING_DECELERATION,
        }

    def _physics_acceleration(self, lead_vehicle):
        if self.physics_model is None:
            return self.acceleration
        return self.physics_model.compute_acceleration(self, lead_vehicle)

    def _braking_deceleration(self, environment):
        if hasattr(self.braking_strategy, "braking_deceleration"):
            return self.braking_strategy.braking_deceleration(self, environment)
        return environment["braking_deceleration"]

    def _clamp_acceleration(self, acceleration):
        return max(self.MIN_ACCELERATION, min(self.MAX_ACCELERATION, float(acceleration)))
