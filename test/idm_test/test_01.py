import math
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from physics.idm_model import IDMModel


class DummyVehicle:
    def __init__(self, position, velocity):
        self.position = position
        self.velocity = velocity


def test_idm_free_road_acceleration_at_rest_is_maximum():
    model = IDMModel()
    vehicle = DummyVehicle(position=0.0, velocity=0.0)

    acceleration = model.compute_acceleration(vehicle, None)

    assert math.isclose(acceleration, model.max_acceleration)


def test_idm_free_road_acceleration_drops_to_zero_at_desired_speed():
    model = IDMModel()
    vehicle = DummyVehicle(position=0.0, velocity=model.desired_velocity)

    acceleration = model.compute_acceleration(vehicle, None)

    assert math.isclose(acceleration, 0.0, abs_tol=1e-9)


def test_idm_responds_to_close_lead_vehicle_with_braking():
    model = IDMModel()
    vehicle = DummyVehicle(position=10.0, velocity=15.0)
    lead = DummyVehicle(position=22.0, velocity=5.0)

    acceleration = model.compute_acceleration(vehicle, lead)

    assert acceleration < 0.0
    assert acceleration >= -model.comfortable_braking


def test_idm_handles_zero_gap_without_crashing():
    model = IDMModel()
    vehicle = DummyVehicle(position=10.0, velocity=12.0)
    lead = DummyVehicle(position=10.0, velocity=12.0)

    acceleration = model.compute_acceleration(vehicle, lead)

    assert acceleration == -model.comfortable_braking


def run_with_logs() -> None:
    tests = [
        test_idm_free_road_acceleration_at_rest_is_maximum,
        test_idm_free_road_acceleration_drops_to_zero_at_desired_speed,
        test_idm_responds_to_close_lead_vehicle_with_braking,
        test_idm_handles_zero_gap_without_crashing,
    ]

    print("Running IDM model tests...")
    for test_func in tests:
        test_func()
        print(f"PASS: {test_func.__name__}")
    print("All IDM model tests passed.")


if __name__ == "__main__":
    run_with_logs()
