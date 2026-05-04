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
        3. Choose the closest constraint (signal or real lead vehicle)
        4. Otherwise use the real lead vehicle
        
        Args:
            dt: Time step in seconds
        """
        # Step A: Get signal (simplified - use first signal if available)
        signal = self.signals[0] if self.signals else None
        
        # Step B: Extract signal position robustly
        sig_pos = None
        if signal:
            pos = getattr(signal, "position", None)
            sig_pos = pos[0] if isinstance(pos, tuple) else pos
        
        # Update all vehicles with signal-aware logic
        for vehicle in self.vehicles:
            # Ensure vehicle is in a lane (has lane context)
            if not vehicle.lane:
                continue
            
            vehicle_pos = getattr(vehicle, "position", None)
            if vehicle_pos is None:
                continue
            
            # Step C: Get the real lead vehicle from the lane
            lead_vehicle = vehicle.lane.get_lead_vehicle(vehicle)
            
            # Step D: Determine effective lead (signal vs real lead vehicle)
            effective_lead = lead_vehicle
            signal_is_active = False
            
            # Check if signal should influence vehicle
            if signal and sig_pos is not None and signal.is_red():
                if vehicle_pos < sig_pos:
                    # Signal is ahead of vehicle
                    virtual_lead = VirtualLead(sig_pos)
                    
                    # Choose the closest constraint ahead
                    if lead_vehicle is None:
                        # No real lead vehicle, use signal
                        effective_lead = virtual_lead
                        signal_is_active = True
                    else:
                        # Compare signal vs lead vehicle position
                        lead_pos = getattr(lead_vehicle, "position", None)
                        if lead_pos is None or sig_pos < lead_pos:
                            # Signal is closer than lead vehicle
                            effective_lead = virtual_lead
                            signal_is_active = True
            
            # Step E: Debug logging
            print(
                f"Signal influence={'YES' if signal_is_active else 'NO'} "
                f"sig_pos={sig_pos} vehicle_pos={vehicle_pos}"
            )
            
            # Step F: Update vehicle with effective lead
            vehicle.update(dt, effective_lead)

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
