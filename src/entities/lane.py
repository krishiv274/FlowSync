from typing import Callable, Optional, Protocol, runtime_checkable


@runtime_checkable
class VehicleLike(Protocol):
    position: float
    lane: object

    def update(self, dt: float, lead_vehicle: Optional["VehicleLike"]) -> None:
        ...


class Lane:
    def __init__(self, lane_id, length=1000, width=3.5, update_fn: Optional[Callable[[VehicleLike, float, Optional[VehicleLike]], None]] = None):
        self.id = lane_id
        self.length = length
        self.width = width
        self.vehicles = []
        self.intersection = None
        self._update_fn = update_fn or (lambda vehicle, dt, lead: vehicle.update(dt, lead))

    def add_vehicle(self, vehicle):
        if vehicle in self.vehicles:
            return False

        vehicle.lane = self
        if not hasattr(vehicle, 'position'):
            vehicle.position = 0.0

        if vehicle.position < 0:
            raise ValueError("Invalid position")

        self.vehicles.append(vehicle)
        return True

    def set_intersection(self, intersection):
        self.intersection = intersection

    def set_update_fn(self, update_fn: Callable[[VehicleLike, float, Optional[VehicleLike]], None]) -> None:
        self._update_fn = update_fn

    def remove_vehicle(self, vehicle):
        if vehicle in self.vehicles:
            self.vehicles.remove(vehicle)
            vehicle.lane = None
            return True
        return False

    def sort_vehicles(self):
        # Sort back (lowest position) to front for deterministic lead lookup.
        self.vehicles.sort(key=lambda v: getattr(v, 'position', 0.0))

    def get_lead_vehicle(self, vehicle):
        vehicle_pos = getattr(vehicle, 'position', 0.0)
        lead = None
        lead_gap = None

        for candidate in self.vehicles:
            if candidate is vehicle:
                continue

            candidate_pos = getattr(candidate, 'position', 0.0)
            gap = candidate_pos - vehicle_pos
            if gap <= 0:
                continue

            if lead_gap is None or gap < lead_gap:
                lead = candidate
                lead_gap = gap

        return lead

    def distance_to_end(self, vehicle):
        pos = getattr(vehicle, 'position', 0.0)
        return max(0, self.length - pos)

    def update(self, dt):
        # Maintain deterministic vehicle ordering once per tick.
        self.sort_vehicles()
        for vehicle in list(self.vehicles):
            lead = self.get_lead_vehicle(vehicle)
            self._update_vehicle(vehicle, dt, lead)

        # Debug-only invariant to catch ordering regressions during integration.
        assert all(
            self.vehicles[i].position <= self.vehicles[i + 1].position
            for i in range(len(self.vehicles) - 1)
        )

    def _update_vehicle(self, vehicle, dt, lead):
        self._update_fn(vehicle, dt, lead)