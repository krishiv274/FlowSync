"""Scene builder for a presentation-ready crossroad simulation."""

from __future__ import annotations

from entities.intersection import Intersection
from entities.lane import Lane
from entities.road import Road
from entities.traffic_signal import TrafficSignal
from factory.vehicle_factory import VehicleFactory
from physics.braking.braking_system import BrakingSystem


INTERSECTION_START = 350.0
STOP_LINE_POSITION = 332.0
EXIT_POSITION = 850.0
SPAWN_GAP = 120.0
MAX_VEHICLES_PER_DEMO_LANE = 3
ACTIVE_DEMO_DIRECTIONS = ("WEST_EAST", "NORTH_SOUTH")
QUEUE_GAP = 62.0


class CoordinatedIntersection(Intersection):
    """Intersection with horizontal and vertical signals on opposite phases."""

    PHASES = (
        "HORIZONTAL_GREEN",
        "HORIZONTAL_YELLOW",
        "VERTICAL_GREEN",
        "VERTICAL_YELLOW",
    )
    PHASE_DURATIONS = {
        "HORIZONTAL_GREEN": 14.0,
        "HORIZONTAL_YELLOW": 3.0,
        "VERTICAL_GREEN": 14.0,
        "VERTICAL_YELLOW": 3.0,
    }
    PHASE_STATES = {
        "HORIZONTAL_GREEN": ("GREEN", "RED"),
        "HORIZONTAL_YELLOW": ("YELLOW", "RED"),
        "VERTICAL_GREEN": ("RED", "GREEN"),
        "VERTICAL_YELLOW": ("RED", "YELLOW"),
    }

    def __init__(self, intersection_id, horizontal_signal, vertical_signal):
        super().__init__(intersection_id)
        self.horizontal_signal = horizontal_signal
        self.vertical_signal = vertical_signal
        self.phase_index = 0
        self.phase = self.PHASES[self.phase_index]
        self.timer = self.PHASE_DURATIONS[self.phase]
        self._apply_phase(notify=False)

    def update(self, dt):
        if dt < 0:
            raise ValueError("dt must be non-negative")

        self.timer -= dt
        while self.timer <= 0:
            overflow = -self.timer
            self.phase_index = (self.phase_index + 1) % len(self.PHASES)
            self.phase = self.PHASES[self.phase_index]
            self.timer = self.PHASE_DURATIONS[self.phase] - overflow
            self._apply_phase()
        self.horizontal_signal.timer = self.timer
        self.vertical_signal.timer = self.timer

    def _apply_phase(self, notify=True):
        horizontal_state, vertical_state = self.PHASE_STATES[self.phase]
        self._set_signal_state(self.horizontal_signal, horizontal_state, notify)
        self._set_signal_state(self.vertical_signal, vertical_state, notify)

    def _set_signal_state(self, signal, state, notify):
        changed = signal.state != state
        signal.state = state
        signal.timer = self.timer
        if notify and changed:
            signal.notify()


def _make_lane(lane_id, direction, length=800):
    lane = Lane(lane_id=lane_id, length=length, update_fn=_update_demo_vehicle)
    lane.render_direction = direction
    return lane


def _update_demo_vehicle(vehicle, dt, lead):
    lane = getattr(vehicle, "lane", None)
    signal = lane.intersection.get_signal_for_lane(lane) if lane and lane.intersection else None
    distance_to_signal = None

    if signal is not None and vehicle.position < STOP_LINE_POSITION:
        signal_position = signal.position[0]
        stop_target = signal_position
        if lead is not None:
            stop_target = min(stop_target, lead.position - QUEUE_GAP)
        distance_to_signal = max(0.0, stop_target - vehicle.position)

    vehicle.update(dt, lead, distance_to_signal=distance_to_signal)
    if (
        lead is not None
        and vehicle.position < STOP_LINE_POSITION
        and lead.position < STOP_LINE_POSITION
        and vehicle.position > lead.position - QUEUE_GAP
    ):
        vehicle.position = max(0.0, lead.position - QUEUE_GAP)
        vehicle.velocity = 0.0


def _make_vehicle(lane, direction, position=0.0, velocity=10.0):
    vehicle = VehicleFactory.create_vehicle("car")
    vehicle.position = float(position)
    vehicle.velocity = float(velocity)
    vehicle.render_direction = direction
    vehicle.braking_strategy = BrakingSystem(stop_distance=80.0)
    lane.add_vehicle(vehicle)
    return vehicle


def spawn_demo_vehicle(lane, position=0.0, velocity=10.0):
    """Create a demo vehicle for a render-aware lane."""
    direction = getattr(lane, "render_direction", "WEST_EAST")
    return _make_vehicle(lane, direction, position=position, velocity=velocity)


def build_simple_intersection():
    """Create roads, lanes, vehicles, and coordinated traffic lights for demo."""
    horizontal_road = Road(road_id=1, length=800)
    vertical_road = Road(road_id=2, length=800)

    west_to_east = _make_lane("west_to_east", "WEST_EAST")
    east_to_west = _make_lane("east_to_west", "EAST_WEST")
    north_to_south = _make_lane("north_to_south", "NORTH_SOUTH")
    south_to_north = _make_lane("south_to_north", "SOUTH_NORTH")

    horizontal_road.add_lane(west_to_east)
    horizontal_road.add_lane(east_to_west)
    vertical_road.add_lane(north_to_south)
    vertical_road.add_lane(south_to_north)

    horizontal_signal = TrafficSignal(signal_id=1, position=(STOP_LINE_POSITION, 400))
    horizontal_signal.render_group = "HORIZONTAL"
    vertical_signal = TrafficSignal(signal_id=2, position=(STOP_LINE_POSITION, 400))
    vertical_signal.render_group = "VERTICAL"

    intersection = CoordinatedIntersection(1, horizontal_signal, vertical_signal)

    for lane in (west_to_east, east_to_west):
        lane.set_intersection(intersection)
        intersection.add_signal(lane, horizontal_signal)
    for lane in (north_to_south, south_to_north):
        lane.set_intersection(intersection)
        intersection.add_signal(lane, vertical_signal)

    vehicles = [
        spawn_demo_vehicle(west_to_east, position=0.0, velocity=10.0),
        spawn_demo_vehicle(north_to_south, position=0.0, velocity=10.0),
    ]

    for vehicle in vehicles:
        signal = intersection.get_signal_for_lane(vehicle.lane)
        if signal is not None:
            signal.attach(vehicle)
    horizontal_signal.notify()
    vertical_signal.notify()

    return {
        "roads": [horizontal_road, vertical_road],
        "vehicles": vehicles,
        "signals": [horizontal_signal, vertical_signal],
        "intersections": [intersection],
    }
