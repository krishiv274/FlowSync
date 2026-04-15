class Vehicle:
    def __init__(self, position, velocity, physics_model, acceleration=0):
        self.position = position
        self.velocity = velocity
        self.acceleration = acceleration
        self.physics_model = physics_model

    def update(self, dt, lead=None):
        self.acceleration = self.physics_model.compute_acceleration(self, lead)

        self.velocity += self.acceleration * dt

        if self.velocity < 0:
            self.velocity = 0

        self.position += self.velocity * dt
