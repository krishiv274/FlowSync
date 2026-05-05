from src.entities.lane import Lane
from src.entities.road import Road


class LaneFactory:
    @staticmethod
    def create_standard_lane(lane_id, length=1000):
        return Lane(lane_id, length=length, width=3.5)


def create_straight_road(road_id=1, num_lanes=2, length=1000):
    road = Road(road_id, length)

    for i in range(num_lanes):
        lane = LaneFactory.create_standard_lane(i, length=length)
        road.add_lane(lane)

    return road
