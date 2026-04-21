from src.entities.lane import Lane
from utils.debug_tools import check_no_overlap, check_sorted


class MockVehicle:
    """Minimal vehicle stub for deterministic lead-order testing."""

    def __init__(self, vehicle_id, position):
        self.id = vehicle_id
        self.position = position
        self.lane = None

    def update(self, dt, lead_vehicle):
        if lead_vehicle is None:
            self.position += 0.7 * dt
            return

        gap = lead_vehicle.position - self.position
        # Move forward but preserve a minimum spacing envelope.
        self.position += max(0.0, min(0.4 * dt, gap - 0.5))


def _assert_lead_chain_matches_sorted_order(lane):
    for index, vehicle in enumerate(lane.vehicles):
        expected_lead = lane.vehicles[index + 1] if index + 1 < len(lane.vehicles) else None
        assert lane.get_lead_vehicle(vehicle) is expected_lead


def test_dynamic_lead_remains_correct_across_updates():
    lane = Lane(1, length=1000)
    vehicles = [
        MockVehicle(1, 2.0),
        MockVehicle(2, 6.0),
        MockVehicle(3, 10.0),
        MockVehicle(4, 14.0),
        MockVehicle(5, 18.0),
    ]

    for vehicle in vehicles:
        lane.add_vehicle(vehicle)

    for _ in range(8):
        lane.update(dt=1.0)
        check_sorted(lane)
        check_no_overlap(lane, min_gap=0.5)
        _assert_lead_chain_matches_sorted_order(lane)
