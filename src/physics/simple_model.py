class SimpleModel:
    def __init__(self):
        self.safe_distance = 10.0
        self.k_gap = 0.5  # how strongly we react to distance
        self.k_speed = 0.8  # how strongly we react to relative speed
        self.max_acc = 3.0
        self.min_acc = -5.0

    def compute_acceleration(self, vehicle, lead):
        if lead:
            gap = lead.position - vehicle.position
            relative_speed = vehicle.velocity - lead.velocity

            acc = (self.k_gap * (gap - self.safe_distance)) - (self.k_speed * relative_speed)
        else:
            # free road
            acc = 2.0

        if acc > self.max_acc:
            acc = self.max_acc
        elif acc < self.min_acc:
            acc = self.min_acc

        return acc
