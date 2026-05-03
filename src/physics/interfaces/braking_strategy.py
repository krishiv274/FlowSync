"""Interface for vehicle braking strategies."""

from abc import ABC, abstractmethod


class IBrakingStrategy(ABC):
	@abstractmethod
	def should_brake(self, vehicle, environment):
		"""Return True when the vehicle should brake."""
		raise NotImplementedError

	def shouldBrake(self, vehicle, environment):
		"""Compatibility alias for older camelCase call sites."""
		return self.should_brake(vehicle, environment)

