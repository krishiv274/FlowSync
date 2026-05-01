import os
import sys

# Ensure project root is on sys.path so `src` can be imported when running tests directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.entities.traffic_signal import TrafficSignal


class DummyVehicle:
    def __init__(self):
        self.received = []

    def on_signal_change(self, state):
        self.received.append(state)


class PrintingVehicle:
    def __init__(self, name):
        self.name = name

    def on_signal_change(self, state):
        print(f"{self.name} received: {state}")


def test_traffic_signal_notifies_observers():
    signal = TrafficSignal(1, (0, 0))
    v = DummyVehicle()
    signal.attach(v)

    # Trigger three state transitions: RED -> GREEN -> YELLOW -> RED
    signal.update(10)
    signal.update(10)
    signal.update(10)

    assert v.received == [TrafficSignal.GREEN, TrafficSignal.YELLOW, TrafficSignal.RED]


def test_complete_working_flow_demo():
    """Demonstrate full attach/notify/detach flow with prints for manual inspection.

    This is intended as a runnable demonstration showing:
    - attaching multiple observers
    - receiving notifications for each state change
    - detaching an observer
    - handling a large dt that advances multiple states
    """
    signal = TrafficSignal(2, (10, 10))

    p1 = PrintingVehicle("VehicleA")
    p2 = PrintingVehicle("VehicleB")
    collector = DummyVehicle()

    print("Initial:", signal)

    # Attach two printing vehicles and one collector
    signal.attach(p1)
    signal.attach(p2)
    signal.attach(collector)

    # Advance by one full RED cycle to GREEN
    print("-- update(10) --")
    signal.update(10)

    # Advance to YELLOW
    print("-- update(10) --")
    signal.update(10)

    # Advance to RED
    print("-- update(10) --")
    signal.update(10)

    # Detach VehicleB and advance by a large dt that may cause multiple transitions
    print("Detaching VehicleB")
    signal.detach(p2)

    print("-- update(25) (large dt causing multiple transitions) --")
    signal.update(25)

    # Collector should have recorded notifications; VehicleB should stop receiving prints
    assert TrafficSignal.GREEN in collector.received
    assert TrafficSignal.YELLOW in collector.received


if __name__ == "__main__":
    test_traffic_signal_notifies_observers()
    print("test_traffic_signal_notifies_observers: OK")
    print()
    test_complete_working_flow_demo()
    print("test_complete_working_flow_demo: OK")
