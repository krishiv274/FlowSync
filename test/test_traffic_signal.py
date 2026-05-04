import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from entities.traffic_signal import TrafficSignal


def test_signal_state_constants_exist():
    assert TrafficSignal.RED == "RED"
    assert TrafficSignal.GREEN == "GREEN"
    assert TrafficSignal.YELLOW == "YELLOW"


def test_signal_init_defaults():
    signal = TrafficSignal(signal_id=10, position=(1.0, 2.0))

    assert signal.id == 10
    assert signal.position == (1.0, 2.0)
    assert signal.state == TrafficSignal.RED
    assert signal.timer == signal.cycle_times[TrafficSignal.RED]


def test_change_state_sequence():
    signal = TrafficSignal(
        signal_id=1,
        position=(0.0, 0.0),
        cycle_times={
            TrafficSignal.RED: 1.0,
            TrafficSignal.GREEN: 1.0,
            TrafficSignal.YELLOW: 1.0,
        },
    )

    signal.change_state()
    assert signal.state == TrafficSignal.GREEN
    assert signal.timer == 1.0

    signal.change_state()
    assert signal.state == TrafficSignal.YELLOW
    assert signal.timer == 1.0

    signal.change_state()
    assert signal.state == TrafficSignal.RED
    assert signal.timer == 1.0


def test_update_advances_state_when_timer_elapses():
    signal = TrafficSignal(
        signal_id=20,
        position=(0.0, 0.0),
        cycle_times={
            TrafficSignal.RED: 1.0,
            TrafficSignal.GREEN: 1.0,
            TrafficSignal.YELLOW: 1.0,
        },
    )

    signal.update(1.0)
    assert signal.state == TrafficSignal.GREEN

    signal.update(1.0)
    assert signal.state == TrafficSignal.YELLOW

    signal.update(1.0)
    assert signal.state == TrafficSignal.RED


def test_helper_methods_reflect_state():
    signal = TrafficSignal(
        signal_id=5,
        position=(0.0, 0.0),
        cycle_times={
            TrafficSignal.RED: 1.0,
            TrafficSignal.GREEN: 1.0,
            TrafficSignal.YELLOW: 1.0,
        },
    )

    # initial state is RED
    assert signal.is_red()
    assert not signal.is_green()
    assert not signal.is_yellow()

    # advance to GREEN
    signal.update(1.0)
    assert signal.is_green()
    assert not signal.is_red()
    assert not signal.is_yellow()

    # advance to YELLOW
    signal.update(1.0)
    assert signal.is_yellow()
    assert not signal.is_red()
    assert not signal.is_green()


def run_with_logs() -> None:
    tests = [
        test_signal_state_constants_exist,
        test_signal_init_defaults,
        test_change_state_sequence,
        test_update_advances_state_when_timer_elapses,
    ]
    print("Running traffic signal tests...")
    for test_func in tests:
        test_func()
        print(f"PASS: {test_func.__name__}")
    print("All traffic signal tests passed.")


def run_example() -> None:
    print("\nExample: TrafficSignal running for 15 seconds")
    signal = TrafficSignal(signal_id=99, position=(0.0, 0.0))
    for second in range(1, 16):
        signal.update(1.0)
        print(f"t={second:02d}s -> state={signal.state}, timer={signal.timer:.2f}")


if __name__ == "__main__":
    run_with_logs()
    run_example()
