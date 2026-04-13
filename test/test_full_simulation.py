from src.entities.intersection import Intersection
from src.entities.traffic_signal import TrafficSignal
from src.simulation.road_builder import create_straight_road
from utils.debug_tools import check_no_overlap, check_sorted


class MockVehicle:
    def __init__(self, vid, position):
        self.id = vid
        self.position = position
        self.lane = None

    def update(self, dt, lead_vehicle):
        self.position += 1


def test_full_simulation_integration():
    road = create_straight_road(num_lanes=2, length=1000)
    lane = road.get_lane(0)

    vehicles = [
        MockVehicle(1, 30),
        MockVehicle(2, 10),
        MockVehicle(3, 50),
        MockVehicle(4, 20),
        MockVehicle(5, 40),
    ]

    for vehicle in vehicles:
        lane.add_vehicle(vehicle)
        assert vehicle.lane is lane
        assert lane.distance_to_end(vehicle) >= 0

    intersection = Intersection(1)
    signal = TrafficSignal(signal_id=1, position=(0, 0))
    intersection.add_signal(lane, signal)
    lane.set_intersection(intersection)

    assert lane.intersection is intersection
    assert lane.intersection.get_signal_for_lane(lane) is signal

    lead_before_update = lane.get_lead_vehicle(vehicles[1])
    assert lead_before_update is not None
    assert lead_before_update.position > vehicles[1].position

    for _ in range(10):
        road.update(dt=1)
        check_sorted(lane)
        check_no_overlap(lane)

    lead_after_update = lane.get_lead_vehicle(vehicles[1])
    assert lead_after_update is not None
    assert lead_after_update.position > vehicles[1].position
    assert lane.intersection.get_signal_for_lane(lane) is signal


if __name__ == "__main__":
    test_full_simulation_integration()
