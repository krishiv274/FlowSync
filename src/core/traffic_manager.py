"""Traffic simulation manager responsible for vehicles, roads, and signals."""

from entities.road import Road
from entities.lane import Lane
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

        # Create a traffic signal
        signal = TrafficSignal(signal_id=1, position=(500, 500))
        self.signals.append(signal)
        for vehicle in self.vehicles:
            self._attach_vehicle_to_signals(vehicle)
        signal.notify()

    def update(self, dt):
        """Update all traffic entities.
        
        Args:
            dt: Time step in seconds
        """
        self.update_signals(dt)
        self.update_vehicles(dt)

    def update_vehicles(self, dt):
        """Update all vehicles in the simulation using the Road/Lane update path.

        Args:
            dt: Time step in seconds
        """
        signal = self.signals[0] if self.signals else None
        sig_pos = self._signal_position(signal)
        update_fn = self._build_lane_update_fn(sig_pos)

        for road in self.roads:
            for lane in road.lanes:
                lane.set_update_fn(update_fn)
            road.update(dt)

    def update_signals(self, dt):
        """Update all traffic signals.
        
        Args:
            dt: Time step in seconds
        """
        for signal in self.signals:
            signal.update(dt)

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

    def _signal_position(self, signal):
        if signal is None:
            return None
        pos = getattr(signal, "position", None)
        return pos[0] if isinstance(pos, tuple) else pos

    def _build_lane_update_fn(self, sig_pos):
        def update_fn(vehicle, dt, lead):
            distance_to_signal = self._distance_to_signal(vehicle, sig_pos)
            vehicle.update(dt, lead, distance_to_signal=distance_to_signal)

        return update_fn

    def _distance_to_signal(self, vehicle, sig_pos):
        if sig_pos is None:
            return None

        vehicle_pos = getattr(vehicle, "position", None)
        if vehicle_pos is None:
            return None

        if vehicle_pos >= sig_pos:
            return None

        return sig_pos - vehicle_pos
