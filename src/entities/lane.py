class Lane:
    def __init__(self, lane_id, length=1000, width=3.5):
        self.id = lane_id
        self.length = length
        self.width = width
        self.vehicles = []
        self.intersection = None

    def add_vehicle(self, vehicle):
        vehicle.lane = self
        self.vehicles.append(vehicle)
        self.sort_vehicles()

    def set_intersection(self, intersection):
        self.intersection = intersection

    def remove_vehicle(self, vehicle):
        if vehicle in self.vehicles:
            self.vehicles.remove(vehicle)
            vehicle.lane = None

    def sort_vehicles(self):
        self.vehicles.sort(key=lambda v: v.position)

    def get_lead_vehicle(self, vehicle):
        for i, v in enumerate(self.vehicles):
            if v == vehicle:
                if i + 1 < len(self.vehicles):
                    return self.vehicles[i + 1]
                return None
        return None

    def distance_to_end(self, vehicle):
        return max(0, self.length - vehicle.position)

    def update(self, dt):
        self.sort_vehicles()
        vehicles_copy = self.vehicles[:]

        for vehicle in vehicles_copy:
            lead = self.get_lead_vehicle(vehicle)
            vehicle.update(dt, lead)