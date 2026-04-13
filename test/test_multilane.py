from src.simulation.road_builder import create_straight_road
from utils.debug_tools import check_sorted
from utils.debug_tools import check_no_overlap


class Vehicle:
    def __init__(self, vehicle_id, position):
        self.id = vehicle_id
        self.position = position
        self.lane = None

    def update(self, dt, lead_vehicle):
        self.position += 1


def test_multilane_sorting_and_leads():
    road = create_straight_road(num_lanes=2, length=500)
    lane_a = road.get_lane(0)
    lane_b = road.get_lane(1)

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

    for vehicle in (a1, a2, a3):
        assert vehicle.lane is lane_a
        assert lane_a.distance_to_end(vehicle) >= 0

    for vehicle in (b1, b2, b3):
        assert vehicle.lane is lane_b
        assert lane_b.distance_to_end(vehicle) >= 0

    check_sorted(lane_a)
    check_sorted(lane_b)
    check_no_overlap(lane_a)
    check_no_overlap(lane_b)

    assert [v.position for v in lane_a.vehicles] == [50, 100, 150]
    assert [v.position for v in lane_b.vehicles] == [20, 80, 120]

    assert lane_a.get_lead_vehicle(a2) is a1
    assert lane_a.get_lead_vehicle(a1) is a3
    assert lane_a.get_lead_vehicle(a3) is None

    assert lane_b.get_lead_vehicle(b2) is b1
    assert lane_b.get_lead_vehicle(b1) is b3
    assert lane_b.get_lead_vehicle(b3) is None

    lane_a_positions_before = [v.position for v in lane_a.vehicles]
    lane_b_positions_before = [v.position for v in lane_b.vehicles]

    lane_a.update(dt=1)
    check_sorted(lane_a)
    check_no_overlap(lane_a)

    lane_a_positions_after = [v.position for v in lane_a.vehicles]
    lane_b_positions_after = [v.position for v in lane_b.vehicles]

    assert lane_a_positions_after != lane_a_positions_before
    assert lane_b_positions_after == lane_b_positions_before


if __name__ == "__main__":
    test_multilane_sorting_and_leads()
