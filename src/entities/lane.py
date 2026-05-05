from typing import Callable, Optional, Protocol, runtime_checkable


@runtime_checkable
class VehicleLike(Protocol):
    position: float
    lane: object

    def update(self, dt: float, lead_vehicle: Optional["VehicleLike"]) -> None:
        ...


class UpdateStrategy:
    def update(self, vehicle: VehicleLike, dt: float, lead: Optional[VehicleLike]) -> None:
        raise NotImplementedError


class DefaultUpdateStrategy(UpdateStrategy):
    def update(self, vehicle: VehicleLike, dt: float, lead: Optional[VehicleLike]) -> None:
        vehicle.update(dt, lead)


class _CallableUpdateStrategy(UpdateStrategy):
    def __init__(self, update_fn: Callable[[VehicleLike, float, Optional[VehicleLike]], None]) -> None:
        self._update_fn = update_fn

    def update(self, vehicle: VehicleLike, dt: float, lead: Optional[VehicleLike]) -> None:
        self._update_fn(vehicle, dt, lead)


class Lane:
    def __init__(self, lane_id, length=1000, width=3.5, strategy: Optional[UpdateStrategy] = None, update_fn: Optional[Callable[[VehicleLike, float, Optional[VehicleLike]], None]] = None):
        self.id = lane_id
        self.length = length
        self.width = width
        self.vehicles = []
        self.intersection = None
        if strategy is not None:
            self.strategy = strategy
        elif update_fn is not None:
            self.strategy = _CallableUpdateStrategy(update_fn)
        else:
            self.strategy = DefaultUpdateStrategy()

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
        self.strategy = _CallableUpdateStrategy(update_fn)

    def set_update_strategy(self, strategy: UpdateStrategy) -> None:
        self.strategy = strategy

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
        self._pre_update()
        self._process_vehicles(dt)
        self._post_update()

    def _pre_update(self):
        # Maintain deterministic vehicle ordering once per tick.
        self.sort_vehicles()

    def _process_vehicles(self, dt):
        for vehicle in list(self.vehicles):
            lead = self.get_lead_vehicle(vehicle)
            self._update_vehicle(vehicle, dt, lead)

    def _post_update(self):
        # Debug-only invariant to catch ordering regressions during integration.
        assert all(
            self.vehicles[i].position <= self.vehicles[i + 1].position
            for i in range(len(self.vehicles) - 1)
        )

    def _update_vehicle(self, vehicle, dt, lead):
        """Update a single vehicle with lead vehicle and signal awareness.
        
        Args:
            vehicle: The vehicle to update
            dt: Time step
            lead: The lead vehicle (if any)
        """
        # Calculate distance to signal if intersection exists
        distance_to_signal = None
        if self.intersection is not None:
            signal = self.intersection.get_signal_for_lane(self)
            if signal is not None:
                signal_pos = getattr(signal, "position", (0, 0))
                if isinstance(signal_pos, tuple) and len(signal_pos) >= 1:
                    signal_x = signal_pos[0]
                    vehicle_pos = getattr(vehicle, "position", 0.0)
                    if vehicle_pos < signal_x:
                        distance_to_signal = signal_x - vehicle_pos
        
        # Update vehicle with lead and signal info
        if hasattr(vehicle, 'update'):
            vehicle.update(dt, lead=lead, distance_to_signal=distance_to_signal)
        else:
            self.strategy.update(vehicle, dt, lead)