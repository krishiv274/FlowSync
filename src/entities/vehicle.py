class Vehicle:
    def __init__(self, position, velocity, physics_model=None, acceleration=0, braking_strategy=None):
        self.position = position
        self.velocity = velocity
        self.acceleration = acceleration
        self.physics_model = physics_model
        self.braking_strategy = braking_strategy
        self.signal_state = None

        if not hasattr(self.physics_model, "compute_acceleration"):
            if isinstance(self.physics_model, (int, float)):
                self.acceleration = float(self.physics_model)
            self.physics_model = None

    def update(self, dt, lead_vehicle=None, distance_to_signal=None, **kwargs):
        if lead_vehicle is None and "lead" in kwargs:
            lead_vehicle = kwargs["lead"]

        if distance_to_signal is None:
            distance_to_signal = self._distance_to_signal_from_lane()

        previous_position = self.position
        # IDM is the default motion model.
        if self.braking_strategy is None:
            if self.physics_model is None:
                self.acceleration = float(self.acceleration)
            else:
                self.acceleration = self.physics_model.compute_acceleration(self, lead_vehicle)
        else:
            # Provide context for braking decisions.
            environment = {
                "lead": lead_vehicle,
                "signal_state": self.signal_state,
                "distance_to_signal": distance_to_signal,
            }
            # Braking is a safety override when required.
            if self.braking_strategy.should_brake(self, environment):
                self.acceleration = self._braking_deceleration(environment)
            elif self.physics_model is None:
                self.acceleration = float(self.acceleration)
            else:
                self.acceleration = self.physics_model.compute_acceleration(self, lead_vehicle)

        self.velocity += self.acceleration * dt

        if self.velocity < 0:
            self.velocity = 0

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

    def _braking_deceleration(self, environment):
        if hasattr(self.braking_strategy, "braking_deceleration"):
            return self.braking_strategy.braking_deceleration(self, environment)

        comfortable_braking = getattr(self.physics_model, "comfortable_braking", 2.0)
        return -abs(comfortable_braking)
