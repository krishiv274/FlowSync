class Vehicle:
    def __init__(self, position, velocity, physics_model, acceleration=0, braking_strategy=None):
        self.position = position
        self.velocity = velocity
        self.acceleration = acceleration
        self.lane = None

        self.idm = physics_model
        self.braking = braking_strategy

    def update(self, dt, lead_vehicle):
        # --- 1. Compute safe gap ---
        if lead_vehicle:
            gap = max(0.1, lead_vehicle.position - self.position)
        else:
            gap = float("inf")

        # --- 2. IDM acceleration (no fallback / enforce correct API) ---
        acc = self.idm.compute_acceleration(self, lead_vehicle, gap)

        # --- 3. Signal awareness ---
        if self.lane and self.lane.intersection:
            signal = self.lane.intersection.get_signal_for_lane(self.lane)

            if signal and signal.state == "RED":
                dist_to_signal = self.lane.distance_to_end(self)

                # Only apply braking when near signal
                if dist_to_signal < 50:
                    brake_acc = self._braking_acceleration(dist_to_signal)
                    acc = min(acc, brake_acc)

        # --- 4. Update kinematics ---
        self.velocity += acc * dt
        self.velocity = max(0, self.velocity)
        self.position += self.velocity * dt

    def _braking_acceleration(self, distance_to_signal):
        # Strong default braking if no strategy provided
        if self.braking is None:
            comfortable_braking = getattr(self.idm, "comfortable_braking", 2.0)
            return -abs(comfortable_braking)

        if hasattr(self.braking, "compute"):
            return self.braking.compute(self, distance_to_signal)

        if hasattr(self.braking, "braking_deceleration"):
            return self.braking.braking_deceleration(self, {"distance_to_signal": distance_to_signal})

        # Fallback safety
        comfortable_braking = getattr(self.idm, "comfortable_braking", 2.0)
        return -abs(comfortable_braking)
