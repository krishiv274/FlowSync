import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from entities.lane import Lane


class Vehicle:
    def __init__(self, vehicle_id, position):
        self.id = vehicle_id
        self.position = position

    def update(self, dt, lead_vehicle):
        return


def test_multilane_sorting_and_leads():
    lane_a = Lane(0, 500)
    lane_b = Lane(1, 500)

    a1 = Vehicle(1, 100)
    a2 = Vehicle(2, 50)
    a3 = Vehicle(3, 150)

    b1 = Vehicle(4, 80)
    b2 = Vehicle(5, 20)
    b3 = Vehicle(6, 120)

    lane_a.add_vehicle(a1)
    lane_a.add_vehicle(a2)
    lane_a.add_vehicle(a3)

    lane_b.add_vehicle(b1)
    lane_b.add_vehicle(b2)
    lane_b.add_vehicle(b3)

    assert [v.position for v in lane_a.vehicles] == [50, 100, 150]
    assert [v.position for v in lane_b.vehicles] == [20, 80, 120]

    assert lane_a.get_lead_vehicle(a2) is a1
    assert lane_a.get_lead_vehicle(a1) is a3
    assert lane_a.get_lead_vehicle(a3) is None

    assert lane_b.get_lead_vehicle(b2) is b1
    assert lane_b.get_lead_vehicle(b1) is b3
    assert lane_b.get_lead_vehicle(b3) is None

    assert a1.lane is lane_a
    assert a2.lane is lane_a
    assert a3.lane is lane_a
    assert b1.lane is lane_b
    assert b2.lane is lane_b
    assert b3.lane is lane_b

    assert lane_a.get_lead_vehicle(a1) is not lane_b.get_lead_vehicle(b1)
