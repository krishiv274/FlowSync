class Vehicle:
    def __init__(self, position, velocity, acceleration=0):
        self.position = position
        self.velocity = velocity
        self.acceleration = acceleration

    def update(self, dt, lead=None):
        self.acceleration = 0
        safe = 5

        if lead:
            gap = lead.position - self.position
            if gap < safe:
                self.acceleration = -5
            else:
                self.acceleration = 1
        else:
            self.acceleration = 2

        self.velocity += self.acceleration * dt

        if self.velocity < 0:
            self.velocity = 0

        self.position += self.velocity * dt
