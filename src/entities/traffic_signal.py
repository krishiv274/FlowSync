"""Traffic signal entity definitions."""

from __future__ import annotations
from typing import Protocol, List


class SignalObserver(Protocol):
	def on_signal_change(self, state: str) -> None:
		...


class TrafficSignal:
	"""Timer-driven traffic signal state machine."""

	RED = "RED"
	GREEN = "GREEN"
	YELLOW = "YELLOW"

	TRANSITIONS = {
		RED: GREEN,
		GREEN: YELLOW,
		YELLOW: RED,
	}

	def __init__(
		self,
		signal_id: int,
		position: tuple[float, float],
		cycle_times: dict[str, float] | None = None,
	) -> None:
		default_cycle_times = {
			self.RED: 10.0,
			self.GREEN: 10.0,
			self.YELLOW: 3.0,
		}
		self.id = signal_id
		self.position = position
		self.cycle_times = default_cycle_times if cycle_times is None else dict(cycle_times)

		for s in (self.RED, self.GREEN, self.YELLOW):
			if s not in self.cycle_times:
				raise ValueError(f"Missing cycle time for state: {s}")
			if self.cycle_times[s] <= 0:
				raise ValueError(f"Cycle time for state {s} must be positive")

		self.state = self.RED
		self.timer = float(self.cycle_times[self.RED])
		# Observer list for vehicles or other listeners
		self.observers: List[SignalObserver] = []

	def update(self, dt: float) -> None:
		"""Advance signal timer and switch state when timer elapses."""
		if dt < 0:
			raise ValueError("dt must be non-negative")

		self.timer -= dt
		while self.timer <= 0:
			overflow = -self.timer
			self.change_state()
			self.timer -= overflow

	def change_state(self) -> None:
		"""Advance through RED -> GREEN -> YELLOW -> RED."""
		self.state = self.TRANSITIONS[self.state]
		self.timer = float(self.cycle_times[self.state])
		# Notify registered observers about the state change
		self.notify()

	def __repr__(self) -> str:
		return f"TrafficSignal(id={self.id}, state={self.state}, timer={self.timer:.2f})"

	def is_red(self) -> bool:
		return self.state == self.RED

	def is_green(self) -> bool:
		return self.state == self.GREEN

	def is_yellow(self) -> bool:
		return self.state == self.YELLOW

	def attach(self, vehicle: SignalObserver) -> None:
		"""Register a vehicle to receive signal updates."""
		if vehicle not in self.observers:
			self.observers.append(vehicle)

	def detach(self, vehicle: SignalObserver) -> None:
		"""Unregister a vehicle."""
		if vehicle in self.observers:
			self.observers.remove(vehicle)

	def notify(self) -> None:
		"""Notify all observers about state change."""
		for vehicle in list(self.observers):
			try:
				vehicle.on_signal_change(self.state)
			except Exception as e:
				# Log observer errors but keep signal state machine running
				print(f"[Signal Warning] Observer error: {e}")

