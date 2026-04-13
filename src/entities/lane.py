class Lane:
    def __init__(self, lane_id, length=1000, width=3.5):
        self.id = lane_id
        self.length = length
        self.width = width
        self.vehicles = []
        self.intersection = None

    def add_vehicle(self, vehicle):
        vehicle.lane = self
        if not hasattr(vehicle, 'position'):
            vehicle.position = 0.0
        self.vehicles.append(vehicle)
        self.sort_vehicles()

    def set_intersection(self, intersection):
        self.intersection = intersection

    def remove_vehicle(self, vehicle):
        if vehicle in self.vehicles:
            self.vehicles.remove(vehicle)
            vehicle.lane = None

    def sort_vehicles(self):
        # Sort front (highest position) to back
        self.vehicles.sort(key=lambda v: getattr(v, 'position', 0.0), reverse=True)

    def get_lead_vehicle(self, vehicle):
        # With descending order, the lead vehicle is the one BEFORE in the list
        for i, v in enumerate(self.vehicles):
            if v == vehicle:
                if i - 1 >= 0:
                    return self.vehicles[i - 1]
                return None
        return None

    def distance_to_end(self, vehicle):
        pos = getattr(vehicle, 'position', 0.0)
        return max(0, self.length - pos)

    def update(self, dt):
        # Ensure ordering before update (safe even if manager already sorted)
        self.sort_vehicles()
        vehicles_copy = self.vehicles[:]

        for vehicle in vehicles_copy:
            lead = self.get_lead_vehicle(vehicle)
            vehicle.update(dt, lead)