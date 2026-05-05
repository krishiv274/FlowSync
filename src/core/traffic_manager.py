"""Traffic simulation manager responsible for vehicles, roads, and signals."""

from physics.braking.braking_system import BrakingSystem
from factory.vehicle_factory import VehicleFactory
from simulation.simple_intersection_scene import (
    ACTIVE_DEMO_DIRECTIONS,
    EXIT_POSITION,
    INTERSECTION_START,
    MAX_VEHICLES_PER_DEMO_LANE,
    SPAWN_GAP,
    build_simple_intersection,
    spawn_demo_vehicle,
)


class TrafficManager:
    """Manages all traffic simulation entities: vehicles, roads, and signals."""

    def __init__(self):
        """Initialize TrafficManager with empty entity lists."""
        self.vehicles = []
        self.roads = []
        self.signals = []
        self.intersections = []
        self.initialize_scene()
        # Scene initialized with at least one road, lane, vehicles, and a signal

    def initialize_scene(self):
        """Create initial simulation scene with roads, lanes, and vehicles."""
        scene = build_simple_intersection()
        self.roads = scene["roads"]
        self.vehicles = scene["vehicles"]
        self.signals = scene["signals"]
        self.intersections = scene["intersections"]

    def update(self, dt):
        """Update all traffic entities in the correct order.
        
        Update order (CRITICAL):
        1. Update all intersections (which update signals)
        2. Update all roads (vehicles react to current signal state)
        
        Args:
            dt: Time step in seconds
        """
        # Step 1: Update all intersections (signals first)
        for intersection in self.intersections:
            intersection.update(dt)
        
        # Step 2: Update all roads (lanes and vehicles)
        for road in self.roads:
            road.update(dt)

        self._maintain_demo_traffic()

    def spawn_vehicle(self):
        """Spawn a new vehicle and add to first lane."""
        if self.roads and self.roads[0].lanes:
            lane = self.roads[0].lanes[0]
            vehicle = VehicleFactory.create_vehicle("car")
            self._configure_vehicle(vehicle)
            if hasattr(vehicle, "position"):
                vehicle.position = 0.0
            lane.add_vehicle(vehicle)
            self.vehicles.append(vehicle)

    def _configure_vehicle(self, vehicle):
        if getattr(vehicle, "braking_strategy", None) is None:
            # Use BrakingSystem with increased stop_distance for better signal visibility
            vehicle.braking_strategy = BrakingSystem(stop_distance=30.0)
        self._attach_vehicle_to_signals(vehicle)

    def _attach_vehicle_to_signals(self, vehicle):
        for signal in self.signals:
            signal.attach(vehicle)

    def _maintain_demo_traffic(self):
        lanes = self._demo_lanes()
        if not lanes:
            return

        self._remove_exited_demo_vehicles()
        self._detach_cleared_demo_vehicles()
        for lane in lanes:
            lane_vehicles = [
                vehicle for vehicle in lane.vehicles
                if getattr(vehicle, "render_direction", None) == lane.render_direction
            ]
            if len(lane_vehicles) >= MAX_VEHICLES_PER_DEMO_LANE:
                continue
            if lane_vehicles and min(vehicle.position for vehicle in lane_vehicles) < SPAWN_GAP:
                continue

            vehicle = spawn_demo_vehicle(lane)
            self.vehicles.append(vehicle)
            signal = lane.intersection.get_signal_for_lane(lane)
            if signal is not None:
                signal.attach(vehicle)
                vehicle.on_signal_change(signal.state)

    def _demo_lanes(self):
        lanes = []
        for road in self.roads:
            for lane in road.lanes:
                if getattr(lane, "render_direction", None) in ACTIVE_DEMO_DIRECTIONS:
                    lanes.append(lane)
        return lanes

    def _remove_exited_demo_vehicles(self):
        for vehicle in list(self.vehicles):
            if not hasattr(vehicle, "render_direction"):
                continue
            if getattr(vehicle, "position", 0.0) <= EXIT_POSITION:
                continue

            lane = getattr(vehicle, "lane", None)
            if lane is not None:
                signal = lane.intersection.get_signal_for_lane(lane) if lane.intersection else None
                if signal is not None:
                    signal.detach(vehicle)
                lane.remove_vehicle(vehicle)

            if vehicle in self.vehicles:
                self.vehicles.remove(vehicle)

    def _detach_cleared_demo_vehicles(self):
        for vehicle in self.vehicles:
            if not hasattr(vehicle, "render_direction"):
                continue
            if getattr(vehicle, "position", 0.0) < INTERSECTION_START:
                continue

            lane = getattr(vehicle, "lane", None)
            if lane is None or lane.intersection is None:
                continue

            signal = lane.intersection.get_signal_for_lane(lane)
            if signal is not None:
                signal.detach(vehicle)
            vehicle.signal_state = None
