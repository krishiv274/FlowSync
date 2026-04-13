"""Traffic signal entity definitions."""

from __future__ import annotations

class TrafficSignal:
	"""Timer-driven traffic signal state machine."""

	RED = "RED"
	GREEN = "GREEN"
	YELLOW = "YELLOW"

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
		if self.state == self.RED:
			self.state = self.GREEN
		elif self.state == self.GREEN:
			self.state = self.YELLOW
		else:
			self.state = self.RED

		self.timer = float(self.cycle_times[self.state])

	def __repr__(self) -> str:
		return f"TrafficSignal(id={self.id}, state={self.state}, timer={self.timer:.2f})"

