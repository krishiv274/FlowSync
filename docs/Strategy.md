## Design Pattern Used: Strategy Pattern

### Overview

The Strategy Pattern is used to define a family of algorithms, encapsulate each one, and make them interchangeable at runtime. This allows the behavior of an object to be selected dynamically without modifying its code.

### Where It Is Used

In this project, the Strategy Pattern is applied to:

1. **Physics Model (IDM)**
2. **Braking System**

### Implementation

#### 1. Physics Strategy

An interface `IPhysicsModel` defines the method:

* `computeAcceleration(vehicle, leadVehicle)`

Concrete implementation:

* `IDMModel` implements the Intelligent Driver Model

#### 2. Braking Strategy

An interface `IBrakingStrategy` defines:

* `shouldBrake(vehicle, environment)`

Concrete implementations:

* `EmergencyBrake`
* `SignalBrake`

### Structure

* `Vehicle` class does NOT implement physics or braking logic directly
* Instead, it holds references to:

  * `IPhysicsModel`
  * `IBrakingStrategy`

This allows behavior to be changed dynamically without modifying the `Vehicle` class.

### Benefits

* **Open/Closed Principle**: New behaviors can be added without modifying existing code
* **Flexibility**: Different driving behaviors can be assigned to vehicles
* **Reusability**: Physics and braking logic are decoupled from vehicle logic
* **Testability**: Each strategy can be tested independently

### Example

```python
vehicle.physics_model = IDMModel()
vehicle.braking_strategy = EmergencyBrake()
```

The same vehicle can later switch to a different strategy without code changes.

### Conclusion

The Strategy Pattern enables modular, extensible, and maintainable design, which is essential for a scalable traffic simulation system.
