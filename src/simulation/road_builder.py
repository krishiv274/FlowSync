from src.entities.lane import Lane
from src.entities.road import Road


def create_straight_road(road_id=1, num_lanes=2, length=1000):
    road = Road(road_id, length)

    for i in range(num_lanes):
        lane = Lane(i, length)
        road.add_lane(lane)

    return road
