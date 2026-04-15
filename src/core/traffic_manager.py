"""Traffic simulation manager responsible for vehicles, roads, and signals."""

from entities.road import Road
from entities.lane import Lane
from entities.traffic_signal import TrafficSignal

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
        """Update all vehicles in the simulation.
        
        Args:
            dt: Time step in seconds
        """
        for road in self.roads:
            for lane in road.lanes:
                # Ensure deterministic order: front (highest position) to back
                if hasattr(lane, "vehicles"):
                    lane.vehicles.sort(key=lambda v: getattr(v, "position", 0.0), reverse=True)
                    # Sanity check that order is still front-to-back.
                    for i in range(len(lane.vehicles) - 1):
                        front = getattr(lane.vehicles[i], "position", None)
                        back = getattr(lane.vehicles[i + 1], "position", None)
                        if front is not None and back is not None and front < back:
                            print(f"WARNING: lane ordering issue front={front} back={back}")
                # Iterate over a snapshot to avoid issues if list mutates
                for vehicle in list(lane.vehicles):
                    lead_vehicle = lane.get_lead_vehicle(vehicle)
                    lead_position = getattr(lead_vehicle, "position", None) if lead_vehicle else None
                    print(
                        f"Vehicle pos={getattr(vehicle, 'position', None)} "
                        f"vel={getattr(vehicle, 'velocity', None)} lead={lead_position}"
                    )
                    vehicle.update(dt, lead_vehicle)

                    # Post-update sanity checks.
                    if getattr(vehicle, "position", None) is None:
                        print("WARNING: vehicle position is None after update")

                    velocity = getattr(vehicle, "velocity", None)
                    if velocity is not None and velocity < 0:
                        print(f"WARNING: negative velocity detected ({velocity}), clamping to 0.0")
                        vehicle.velocity = 0.0

                    print(
                        f"Vehicle updated pos={getattr(vehicle, 'position', None)} "
                        f"vel={getattr(vehicle, 'velocity', None)}"
                    )

    def update_signals(self, dt):
        """Update all traffic signals.
        
        Args:
            dt: Time step in seconds
        """
        for signal in self.signals:
            signal.update(dt)
            print(f"Signal state={getattr(signal, 'state', None)}")
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
