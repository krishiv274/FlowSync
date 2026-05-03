class Vehicle:
    def __init__(self, position, velocity, physics_model, acceleration=0, braking_strategy=None):
        self.position = position
        self.velocity = velocity
        self.acceleration = acceleration
        self.physics_model = physics_model
        self.braking_strategy = braking_strategy
        self.signal_state = None

    def update(self, dt, lead=None, distance_to_signal=None):
        self.acceleration = self.physics_model.compute_acceleration(self, lead)

        if self.braking_strategy is not None:
            environment = {
                "lead": lead,
                "signal_state": self.signal_state,
                "distance_to_signal": distance_to_signal,
            }
            if self.braking_strategy.should_brake(self, environment):
                self.acceleration = self._braking_deceleration()

        self.velocity += self.acceleration * dt

        if self.velocity < 0:
            self.velocity = 0

        self.position += self.velocity * dt

    def on_signal_change(self, state):
        self.signal_state = state

    def _braking_deceleration(self):
        comfortable_braking = getattr(self.physics_model, "comfortable_braking", None)
        if comfortable_braking is None:
            comfortable_braking = getattr(self.physics_model, "comfortable_breaking", 2.0)
        return -abs(comfortable_braking)
