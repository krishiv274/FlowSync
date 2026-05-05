"""Traffic simulation manager responsible for vehicles, roads, and signals."""

from entities.road import Road
from entities.lane import Lane
from entities.intersection import Intersection
from entities.traffic_signal import TrafficSignal
from physics.braking.braking_system import BrakingSystem
from factory.vehicle_factory import VehicleFactory


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
        # Create a road
        road = Road(road_id=1, length=1000)
        self.roads.append(road)

        # Create a lane and add to road
        lane = Lane(lane_id=1, length=1000)
        road.add_lane(lane)

        # Create initial vehicles
        vehicle1 = VehicleFactory.create_vehicle("car")
        self._configure_vehicle(vehicle1)
        if hasattr(vehicle1, "position"):
            vehicle1.position = 0.0
        lane.add_vehicle(vehicle1)
        self.vehicles.append(vehicle1)

        vehicle2 = VehicleFactory.create_vehicle("car")
        self._configure_vehicle(vehicle2)
        if hasattr(vehicle2, "position"):
            vehicle2.position = 20.0  # spaced behind vehicle1
        lane.add_vehicle(vehicle2)
        self.vehicles.append(vehicle2)

        # Create an intersection with a traffic signal
        intersection = Intersection(intersection_id=1)
        self.intersections.append(intersection)
        
        # Create a traffic signal
        signal = TrafficSignal(signal_id=1, position=(500, 500))
        self.signals.append(signal)
        
        # Associate signal with lane in the intersection
        intersection.add_signal(lane, signal)
        lane.set_intersection(intersection)
        
        # Attach all vehicles as observers to the signal
        for vehicle in self.vehicles:
            self._attach_vehicle_to_signals(vehicle)
        signal.notify()

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
            vehicle.braking_strategy = BrakingSystem()
        self._attach_vehicle_to_signals(vehicle)

    def _attach_vehicle_to_signals(self, vehicle):
        for signal in self.signals:
            signal.attach(vehicle)
