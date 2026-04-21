from src.entities.lane import Lane
from src.simulation.road_builder import create_straight_road
from utils.debug_tools import check_no_overlap, check_sorted


class MockVehicle:
    def __init__(self, vehicle_id, position):
        self.id = vehicle_id
        self.position = position
        self.lane = None

    def update(self, dt, lead_vehicle):
        step = 0.05 * dt
        if lead_vehicle is None:
            self.position += step
            return

        if (lead_vehicle.position - self.position) > 0.12:
            self.position += step


def test_stress_100_vehicle_stability_single_lane():
    lane = Lane(1, length=2000)

    vehicles = [MockVehicle(i, i * 0.2) for i in range(100)]
    for vehicle in vehicles:
        lane.add_vehicle(vehicle)

    for _ in range(20):
        lane.update(dt=1)
        check_sorted(lane)
        check_no_overlap(lane, min_gap=0.1)

    assert len(lane.vehicles) == 100
    assert all(v.lane is lane for v in vehicles)

    for vehicle in vehicles:
        lead = lane.get_lead_vehicle(vehicle)
        if lead is None:
            assert vehicle.position == max(v.position for v in lane.vehicles)
        else:
            assert lead.position > vehicle.position


def test_multilane_independence_under_stress():
    road = create_straight_road(num_lanes=2, length=3000)
    lane_a = road.get_lane(0)
    lane_b = road.get_lane(1)

    vehicles_a = [MockVehicle(i, i * 0.25) for i in range(50)]
    vehicles_b = [MockVehicle(i + 1000, i * 0.3) for i in range(50)]

    for vehicle in vehicles_a:
        lane_a.add_vehicle(vehicle)
    for vehicle in vehicles_b:
        lane_b.add_vehicle(vehicle)

    baseline_b = [v.position for v in lane_b.vehicles]

    for _ in range(10):
        lane_a.update(dt=1)
        check_sorted(lane_a)
        check_no_overlap(lane_a, min_gap=0.1)

    after_b = [v.position for v in lane_b.vehicles]
    assert baseline_b == after_b

    for _ in range(10):
        road.update(dt=1)
        check_sorted(lane_a)
        check_sorted(lane_b)
        check_no_overlap(lane_a, min_gap=0.1)
        check_no_overlap(lane_b, min_gap=0.1)
