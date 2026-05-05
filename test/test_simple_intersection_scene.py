import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from simulation.simple_intersection_scene import (
    ACTIVE_DEMO_DIRECTIONS,
    EXIT_POSITION,
    INTERSECTION_START,
    QUEUE_GAP,
    STOP_LINE_POSITION,
    build_simple_intersection,
    spawn_demo_vehicle,
)
from core.traffic_manager import TrafficManager


def test_presentation_scene_has_two_roads_and_two_signals():
    scene = build_simple_intersection()

    assert len(scene["roads"]) == 2
    assert len(scene["intersections"]) == 1
    assert len(scene["signals"]) == 2
    assert sum(len(road.lanes) for road in scene["roads"]) == 4


def test_presentation_signals_are_opposite_and_slow_enough():
    scene = build_simple_intersection()
    intersection = scene["intersections"][0]
    horizontal_signal, vertical_signal = scene["signals"]

    assert horizontal_signal.state == "GREEN"
    assert vertical_signal.state == "RED"
    assert intersection.PHASE_DURATIONS["HORIZONTAL_GREEN"] == 14.0

    intersection.update(14.0)
    assert horizontal_signal.state == "YELLOW"
    assert vertical_signal.state == "RED"

    intersection.update(3.0)
    assert horizontal_signal.state == "RED"
    assert vertical_signal.state == "GREEN"


def test_red_light_vehicle_stops_before_intersection():
    scene = build_simple_intersection()
    vertical_vehicle = next(
        vehicle for vehicle in scene["vehicles"]
        if vehicle.render_direction == "NORTH_SOUTH"
    )
    vertical_vehicle.position = STOP_LINE_POSITION - 1.0
    vertical_vehicle.velocity = 10.0

    vertical_vehicle.update(1.0)

    assert vertical_vehicle.position < STOP_LINE_POSITION
    assert vertical_vehicle.position < INTERSECTION_START
    assert vertical_vehicle.velocity == 0


def test_traffic_manager_respawns_demo_vehicles_after_exit():
    manager = TrafficManager()
    original_vehicles = list(manager.vehicles)
    for vehicle in original_vehicles:
        vehicle.position = EXIT_POSITION + 1.0

    manager.update(0.1)

    active_directions = {
        vehicle.render_direction for vehicle in manager.vehicles
        if hasattr(vehicle, "render_direction")
    }
    assert set(ACTIVE_DEMO_DIRECTIONS).issubset(active_directions)
    assert all(vehicle not in manager.vehicles for vehicle in original_vehicles)


def test_stopped_queue_keeps_gap_between_vehicles():
    scene = build_simple_intersection()
    vertical_signal = scene["signals"][1]
    vertical_vehicle = next(
        vehicle for vehicle in scene["vehicles"]
        if vehicle.render_direction == "NORTH_SOUTH"
    )
    lane = vertical_vehicle.lane
    follower = spawn_demo_vehicle(lane, position=STOP_LINE_POSITION - 10.0, velocity=10.0)
    vertical_signal.attach(follower)
    follower.on_signal_change(vertical_signal.state)

    vertical_vehicle.position = STOP_LINE_POSITION - 1.0
    vertical_vehicle.velocity = 0.0

    lane.update(1.0)

    assert follower.position <= vertical_vehicle.position - QUEUE_GAP
    assert follower.velocity == 0.0


def test_vehicle_past_stop_line_continues_on_red():
    scene = build_simple_intersection()
    vertical_vehicle = next(
        vehicle for vehicle in scene["vehicles"]
        if vehicle.render_direction == "NORTH_SOUTH"
    )
    vertical_vehicle.position = STOP_LINE_POSITION + 4.0
    vertical_vehicle.velocity = 10.0

    vertical_vehicle.update(1.0)

    assert vertical_vehicle.position > STOP_LINE_POSITION + 4.0
    assert vertical_vehicle.velocity > 0.0


def test_manager_detaches_vehicle_after_clearing_intersection():
    manager = TrafficManager()
    vertical_vehicle = next(
        vehicle for vehicle in manager.vehicles
        if vehicle.render_direction == "NORTH_SOUTH"
    )
    vertical_signal = manager.signals[1]
    vertical_vehicle.position = INTERSECTION_START + 1.0

    manager.update(0.1)

    assert vertical_vehicle not in vertical_signal.observers
    assert vertical_vehicle.signal_state is None
