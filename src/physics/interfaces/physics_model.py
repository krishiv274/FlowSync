"""Interface for vehicle physics models."""

from abc import ABC, abstractmethod


class IPhysicsModel(ABC):
    @abstractmethod
    def compute_acceleration(self, vehicle, lead_vehicle):
        """Return the acceleration to apply to a vehicle."""
        raise NotImplementedError
