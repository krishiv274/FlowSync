"""Traffic simulation manager responsible for vehicles, roads, and signals."""

from entities.road import Road
from entities.lane import Lane
from entities.traffic_signal import TrafficSignal


class VirtualLead:
    """Virtual lead vehicle created from traffic signal position.
    
    Used to represent a traffic signal as a stopping constraint
    by simulating it as a lead vehicle in the vehicle update pipeline.
    """
    
    def __init__(self, position):
        """Initialize virtual lead at signal position.
        
        Args:
            position: Position coordinate (x-value for lane-based physics)
        """
        self.position = position

try:
    from factory.vehicle_factory import VehicleFactory
except ImportError:
    from entities.vehicle import Vehicle
    from physics.simple_model import SimpleModel

    class VehicleFactory:
        """Fallback vehicle factory used when default factory import fails."""

        @staticmethod
        def create_vehicle(vehicle_type):
            if vehicle_type.lower().strip() != "car":
                raise ValueError(f"Unknown vehicle type: {vehicle_type}")
            return Vehicle(position=0.0, velocity=0.0, physics_model=SimpleModel())


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
        if hasattr(vehicle1, "position"):
            vehicle1.position = 0.0
        lane.add_vehicle(vehicle1)
        self.vehicles.append(vehicle1)

        vehicle2 = VehicleFactory.create_vehicle("car")
        if hasattr(vehicle2, "position"):
            vehicle2.position = 20.0  # spaced behind vehicle1
        lane.add_vehicle(vehicle2)
        self.vehicles.append(vehicle2)

        # Create a traffic signal
        signal = TrafficSignal(signal_id=1, position=(500, 500))
        self.signals.append(signal)

    def update(self, dt):
        """Update all traffic entities.
        
        Args:
            dt: Time step in seconds
        """
        self.update_signals(dt)
        self.update_vehicles(dt)

    def update_vehicles(self, dt):
        """Update all vehicles in the simulation with signal-aware behavior.
        
        For each vehicle:
        1. Detect if there is a traffic signal ahead
        2. If signal is RED and vehicle is before signal:
           - Treat the signal as a virtual lead vehicle
        3. Otherwise:
           - Use the real lead vehicle
        
        Args:
            dt: Time step in seconds
        """
        # Get signal (simplified - use first signal if available)
        signal = self.signals[0] if self.signals else None
        
        # Update all vehicles with signal-aware logic
        for vehicle in self.vehicles:
            # Ensure vehicle is in a lane (has lane context)
            if not vehicle.lane:
                continue
            
            # Get the real lead vehicle from the lane
            lead_vehicle = vehicle.lane.get_lead_vehicle(vehicle)
            
            # Check if signal exists, is RED, and is ahead of vehicle
            fake_lead = None
            if signal and signal.is_red():
                # Signal position is (x, y) tuple; use x-coordinate for lane position
                signal_x = signal.position[0]
                if vehicle.position < signal_x:
                    # Create virtual lead at signal position
                    fake_lead = VirtualLead(signal_x)
                    print(f"Signal influence: ACTIVE")
            
            if not fake_lead:
                print(f"Signal influence: NONE")
            
            # Update vehicle with either virtual lead or real lead
            vehicle.update(dt, fake_lead if fake_lead else lead_vehicle)

    def update_signals(self, dt):
        """Update all traffic signals.
        
        Args:
            dt: Time step in seconds
        """
        for signal in self.signals:
            signal.update(dt)
            # Notify observers if the signal implements it
            if hasattr(signal, "notify"):
                signal.notify()

    def spawn_vehicle(self):
        """Spawn a new vehicle and add to first lane."""
        if self.roads and self.roads[0].lanes:
            lane = self.roads[0].lanes[0]
            vehicle = VehicleFactory.create_vehicle("car")
            if hasattr(vehicle, "position"):
                vehicle.position = 0.0
            lane.add_vehicle(vehicle)
            self.vehicles.append(vehicle)
