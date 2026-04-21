from src.entities.lane import Lane
from utils.debug_tools import check_no_overlap, check_sorted, print_lane_state


class MockVehicle:
    def __init__(self, vehicle_id, position):
        self.id = vehicle_id
        self.position = position
        self.lane = None

    def update(self, dt, lead_vehicle):
        # Keep motion bounded so close spacing remains stable in this edge scenario.
        if lead_vehicle is None:
            self.position += 0.001 * dt
            return

        gap = lead_vehicle.position - self.position
        if gap > 0.005:
            self.position += 0.001 * dt


def test_very_close_vehicle_spacing_and_leads():
    lane = Lane(1, length=1000)

    vehicles = [
        MockVehicle(1, 10),
        MockVehicle(2, 10.01),
        MockVehicle(3, 10.02),
    ]

    for vehicle in vehicles:
        lane.add_vehicle(vehicle)

    lane.update(dt=1)

    print_lane_state(lane)
    check_sorted(lane)
    check_no_overlap(lane, min_gap=0.005)

    assert [round(v.position, 2) for v in lane.vehicles] == [10.0, 10.01, 10.02]

    assert lane.get_lead_vehicle(vehicles[0]) is vehicles[1]
    assert lane.get_lead_vehicle(vehicles[1]) is vehicles[2]
    assert lane.get_lead_vehicle(vehicles[2]) is None


def test_lane_prevents_duplicate_vehicles():
    lane = Lane(1)
    vehicle = MockVehicle(10, 5)

    first_add = lane.add_vehicle(vehicle)
    second_add = lane.add_vehicle(vehicle)

    assert first_add is True
    assert second_add is False
    assert lane.vehicles.count(vehicle) == 1
    assert vehicle.lane is lane
