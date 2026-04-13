"""Vehicle factory utilities."""

from entities.vehicle import Car
# Future imports can be added here (e.g., Truck, Bike)


class VehicleFactory:
    """Factory for creating vehicle instances."""

    registry = {
        "car": Car,
    }

    @staticmethod
    def create_vehicle(vehicle_type):
        """Create a vehicle of the specified type.
        
        Args:
            vehicle_type: Type of vehicle to create (e.g., "car")
            
        Returns:
            Vehicle instance
        """
        if not isinstance(vehicle_type, str):
            raise TypeError("vehicle_type must be a string")

        vehicle_type = vehicle_type.lower().strip()

        if vehicle_type in VehicleFactory.registry:
            vehicle_class = VehicleFactory.registry[vehicle_type]
            return vehicle_class(x=0, y=0)

        raise ValueError(f"Unknown vehicle type: {vehicle_type}")
