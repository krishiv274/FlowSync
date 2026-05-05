## Design Pattern Used: Strategy Pattern

### Overview

The Strategy Pattern encapsulates interchangeable algorithms behind small interfaces so the caller can switch behavior without changing the owning class.

FlowSync uses this pattern in the vehicle motion pipeline and in lane update handling.

### Where It Is Used

The current strategy points are:

1. physics models through `IPhysicsModel`
2. braking behavior through `IBrakingStrategy`
3. lane update execution through `UpdateStrategy`

### Implementation

#### 1. Physics Strategy

`IPhysicsModel` defines:

- `compute_acceleration(vehicle, lead_vehicle)`

Current concrete implementation:

- `IDMModel`

`Vehicle` delegates acceleration calculation to the selected physics model when one is present.

#### 2. Braking Strategy

`IBrakingStrategy` defines:

- `should_brake(vehicle, environment)`

Current concrete implementation:

- `BrakingSystem`

`Vehicle` asks the braking strategy whether braking should occur before applying the final motion step.

#### 3. Lane Update Strategy

`Lane` can use either:

- the default strategy, which calls `vehicle.update(dt, lead)`
- a custom strategy or callable update function

This keeps lane behavior open for extension without hard-coding a single update policy.

### Structure

- `Vehicle` does not implement physics or braking algorithms directly.
- `Lane` does not hard-code vehicle update behavior.
- Behavior is selected by composition, not inheritance.

### Benefits

- **Open/Closed Principle**: new behaviors can be added without modifying the owning entity.
- **Flexibility**: different driving models can be swapped in.
- **Reusability**: the same strategy can be reused across vehicles or lanes.
- **Testability**: each strategy can be verified independently.

### Example

```python
vehicle.physics_model = IDMModel()
vehicle.braking_strategy = BrakingSystem()
lane.set_update_strategy(custom_strategy)
```

### Conclusion

FlowSync uses the Strategy Pattern to keep motion behavior modular, extensible, and easy to test.
