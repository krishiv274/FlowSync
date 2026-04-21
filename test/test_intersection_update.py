from src.entities.intersection import Intersection
from src.entities.lane import Lane
from src.entities.road import Road
from src.entities.traffic_signal import TrafficSignal
from utils.debug_tools import check_sorted


class MockVehicle:
    """Simple deterministic vehicle used for lane-intersection integration tests."""

    def __init__(self, vehicle_id, position):
        self.id = vehicle_id
        self.position = position
        self.lane = None

    def update(self, dt, lead_vehicle):
        if lead_vehicle is None:
            self.position += 0.5 * dt
            return

        if (lead_vehicle.position - self.position) > 0.6:
            self.position += 0.3 * dt


def test_intersection_mapping_survives_lane_updates():
    road = Road(1, length=800)
    lane = Lane(1, length=800)
    road.add_lane(lane)

    intersection = Intersection(10)
    signal = TrafficSignal(signal_id=20, position=(0.0, 0.0))
    intersection.add_signal(lane, signal)
    lane.set_intersection(intersection)

    vehicles = [
        MockVehicle(1, 5.0),
        MockVehicle(2, 8.0),
        MockVehicle(3, 12.0),
    ]
    for vehicle in vehicles:
        lane.add_vehicle(vehicle)

    initial_positions = [v.position for v in vehicles]

    for _ in range(6):
        road.update(dt=1.0)
        check_sorted(lane)
        assert lane.intersection is intersection
        assert intersection.get_signal_for_lane(lane) is signal

    final_positions = [v.position for v in vehicles]
    assert final_positions != initial_positions
