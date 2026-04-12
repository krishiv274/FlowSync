class Lane:
    def __init__(self, lane_id, length=1000, width=3.5):
        self.id = lane_id
        self.length = length
        self.width = width
        self.vehicles = []

    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)
        self.sort_vehicles()

    def remove_vehicle(self, vehicle):
        if vehicle in self.vehicles:
            self.vehicles.remove(vehicle)

    def sort_vehicles(self):
        self.vehicles.sort(key=lambda v: v.position)

    def get_lead_vehicle(self, vehicle):
        self.sort_vehicles()

        for i, v in enumerate(self.vehicles):
            if v == vehicle:
                if i + 1 < len(self.vehicles):
                    return self.vehicles[i + 1]
                return None
        return None

    def update(self, dt):
        self.sort_vehicles()

        for vehicle in self.vehicles:
            lead = self.get_lead_vehicle(vehicle)
            vehicle.update(dt, lead)