import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from entities.lane import Lane
from entities.road import Road
from entities.intersection import Intersection


# Minimal mock classes (so you don't depend on other members)
class Vehicle:
    def __init__(self, id, position):
        self.id = id
        self.position = position

    def update(self, dt, lead_vehicle):
        # Simple forward movement
        self.position += 1


class TrafficSignal:
    def __init__(self, state="RED"):
        self.state = state


def test_full_system():
    road = Road(1)
    lane = Lane(1)
    road.add_lane(lane)

    v1 = Vehicle(1, 10)
    v2 = Vehicle(2, 30)
    v3 = Vehicle(3, 20)

    lane.add_vehicle(v1)
    lane.add_vehicle(v2)
    lane.add_vehicle(v3)

    lead_v1 = lane.get_lead_vehicle(v1)
    assert lead_v1 is v3
    assert lead_v1.position == 20

    before_positions = [v.position for v in lane.vehicles]
    road.update(dt=1)
    after_positions = [v.position for v in lane.vehicles]
    assert sorted(after_positions) == [11, 21, 31]
    assert after_positions != before_positions

    intersection = Intersection(1)

    signal = TrafficSignal("GREEN")
    intersection.add_signal(lane, signal)

    fetched_signal = intersection.get_signal_for_lane(lane)
    assert intersection.get_signal_for_lane(lane) is not None
    assert fetched_signal.state == "GREEN"


if __name__ == "__main__":
    test_full_system()