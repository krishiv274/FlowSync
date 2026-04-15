class IPhysicsModel:
    def compute_acceleration(self, vehicle, lead_vehicle):
        raise NotImplementedError
