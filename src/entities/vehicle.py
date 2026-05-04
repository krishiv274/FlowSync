class Vehicle:
    def __init__(self, position, velocity, physics_model, acceleration=0, braking_strategy=None):
        self.position = position
        self.velocity = velocity
        self.acceleration = acceleration
        self.lane = None

        self.idm = physics_model
        self.braking = braking_strategy

        # Stability constants.
        self.max_acc = 2.5
        self.max_decel = -5.0
        self.min_gap = 2.0
        self.max_jerk = 6.0

    def update(self, dt, lead_vehicle):
        dt = max(0.0, dt)

        # Lead gap used for IDM stability and overlap safety.
        if lead_vehicle:
            gap = max(0.1, lead_vehicle.position - self.position)
        else:
            gap = float("inf")

        # IDM acceleration with safety clamps.
        try:
            acc = self.idm.compute_acceleration(self, lead_vehicle, gap)
        except TypeError:
            acc = self.idm.compute_acceleration(self, lead_vehicle)

        # Signal-aware braking: treat red signal as a stopped vehicle.
        signal = None
        if self.lane and self.lane.intersection:
            signal = self.lane.intersection.get_signal_for_lane(self.lane)

        if signal and signal.state == "RED":
            dist_to_signal = self.lane.distance_to_end(self)
            acc = min(acc, self._signal_braking_acc(dist_to_signal))

        # Clamp acceleration to realistic limits.
        acc = max(self.max_decel, min(self.max_acc, acc))

        # Smooth sudden changes to avoid oscillations.
        max_delta = self.max_jerk * dt
        if acc > self.acceleration + max_delta:
            acc = self.acceleration + max_delta
        elif acc < self.acceleration - max_delta:
            acc = self.acceleration - max_delta

        # Update velocity and position in order with overshoot protection.
        new_velocity = self.velocity + acc * dt
        if new_velocity < 0:
            # Prevent backward motion and position overshoot.
            if self.velocity > 0 and acc < 0 and dt > 0:
                t_stop = self.velocity / (-acc)
                if t_stop < dt:
                    self.position += self.velocity * t_stop + 0.5 * acc * t_stop * t_stop
            self.velocity = 0.0
        else:
            self.velocity = new_velocity
            self.position += self.velocity * dt

        self.acceleration = acc

        # Guarantee no overlap with the lead vehicle.
        if lead_vehicle:
            max_pos = lead_vehicle.position - self.min_gap
            if self.position > max_pos:
                self.position = max_pos
                self.velocity = min(self.velocity, getattr(lead_vehicle, "velocity", 0.0))

    def _signal_braking_acc(self, distance_to_signal):
        distance = max(0.1, distance_to_signal - self.min_gap)
        if distance <= 0:
            return self.max_decel

        # Kinematic braking to stop before the signal line.
        required = -(self.velocity * self.velocity) / (2.0 * distance)
        return max(self.max_decel, required)