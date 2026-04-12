class Road:
    def __init__(self, road_id, length=1000):
        self.id = road_id
        self.length = length
        self.lanes = []

    def add_lane(self, lane):
        self.lanes.append(lane)

    def get_lane(self, index):
        if 0 <= index < len(self.lanes):
            return self.lanes[index]
        return None

    def get_all_vehicles(self):
        vehicles = []
        for lane in self.lanes:
            vehicles.extend(lane.vehicles)
        return vehicles

    def update(self, dt):
        for lane in self.lanes:
            lane.update(dt)