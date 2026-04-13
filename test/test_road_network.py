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
    print("=== Creating Road + Lane ===")
    road = Road(1)
    lane = Lane(1)
    road.add_lane(lane)

    print("=== Adding Vehicles ===")
    v1 = Vehicle(1, 10)
    v2 = Vehicle(2, 30)
    v3 = Vehicle(3, 20)

    lane.add_vehicle(v1)
    lane.add_vehicle(v2)
    lane.add_vehicle(v3)

    print("Vehicles after sorting:")
    for v in lane.vehicles:
        print(v.position)

    # Expect: 10, 20, 30

    print("\n=== Testing Lead Vehicle ===")
    lead_v1 = lane.get_lead_vehicle(v1)
    print("Lead of v1:", lead_v1.position if lead_v1 else None)
    # Expect: 20

    print("\n=== Testing Road Update ===")
    road.update(dt=1)

    print("Positions after update:")
    for v in lane.vehicles:
        print(v.position)
    # Expect: all positions +1 → 11, 21, 31

    print("\n=== Testing Intersection ===")
    intersection = Intersection(1)

    signal = TrafficSignal("GREEN")
    intersection.add_signal(lane, signal)

    fetched_signal = intersection.get_signal_for_lane(lane)
    print("Signal for lane:", fetched_signal.state)
    assert intersection.get_signal_for_lane(lane) is not None

    # Expect: GREEN

    print("\n=== ALL TESTS COMPLETED ===")


if __name__ == "__main__":
    test_full_system()