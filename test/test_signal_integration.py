import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from entities.traffic_signal import TrafficSignal
from entities.vehicle import Vehicle


class MockPhysics:
    def compute_acceleration(self, vehicle, lead):
        return 0


class MockBraking:
    def should_brake(self, vehicle, env):
        return env["signal_state"] == "RED"

    def braking_deceleration(self, vehicle, env):
        return -5


def test_signal_state_transitions():
    signal = TrafficSignal(1, (0, 0))

    signal.update(10)
    assert signal.state == "GREEN"

    signal.update(10)
    assert signal.state == "YELLOW"

    signal.update(10)
    assert signal.state == "RED"


def test_observer_notification():
    class DummyVehicle:
        def __init__(self):
            self.received = []

        def on_signal_change(self, state):
            self.received.append(state)

    signal = TrafficSignal(1, (0, 0))
    v = DummyVehicle()
    signal.attach(v)

    signal.update(30)
    assert v.received == ["GREEN", "YELLOW", "RED"]


def test_vehicle_receives_signal_state():
    mock_model = MockPhysics()

    vehicle = Vehicle(position=0, velocity=10, physics_model=mock_model)
    vehicle.on_signal_change("RED")

    assert vehicle.signal_state == "RED"


def test_braking_triggered_by_signal():
    mock_model = MockPhysics()

    vehicle = Vehicle(
        position=0,
        velocity=10,
        physics_model=mock_model,
        braking_strategy=MockBraking(),
    )
    vehicle.on_signal_change("RED")

    vehicle.update(1)
    assert vehicle.velocity < 10


def test_full_integration_flow():
    mock_model = MockPhysics()

    signal = TrafficSignal(1, (0, 0))
    vehicle = Vehicle(
        position=0,
        velocity=10,
        physics_model=mock_model,
        braking_strategy=MockBraking(),
    )
    signal.attach(vehicle)

    for _ in range(3):
        signal.update(10)
        vehicle.update(1)

    assert vehicle.signal_state in ["RED", "GREEN", "YELLOW"]
