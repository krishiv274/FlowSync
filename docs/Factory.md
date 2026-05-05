# Factory Pattern - Traffic Simulation System

## Overview

The Factory Pattern centralizes object creation so the rest of the codebase does not need to know the exact construction details of each product.

In FlowSync, this pattern is used to create vehicles in one place and to keep initialization concerns out of the simulation loop.

## Where It Is Used

The current factory usage is in:

- `VehicleFactory.create_vehicle(vehicle_type)`

## What Problem It Solves

Without a factory, simulation code would need to know how to:

- instantiate the correct vehicle class
- assign a unique id
- attach the default physics model
- keep creation logic consistent across spawn points

That would spread construction logic across the core simulation flow.

## Implementation

### Factory Class: `VehicleFactory`

`VehicleFactory` currently acts as the creation point for simulation vehicles.

It does the following:

- normalizes the requested vehicle type
- looks up the constructor in `VehicleFactory.registry`
- creates a `Vehicle`
- attaches `IDMModel` as the default physics model
- assigns a unique id

```python
class VehicleFactory:
    registry = {
        "car": Vehicle,
    }

    @staticmethod
    def create_vehicle(vehicle_type):
        ...
```

### Product

The current concrete product is:

- `Vehicle`

The factory is already structured so additional vehicle classes can be added later by extending the registry.

## Interaction Flow

1. `TrafficManager` requests a new vehicle.
2. `VehicleFactory.create_vehicle("car")` is called.
3. The factory resolves the registered class.
4. A `Vehicle` instance is returned with default behavior attached.
5. `TrafficManager` configures lane position and signal observers.

## Benefits

- **Encapsulation**: creation details stay in one place.
- **Consistency**: every spawned vehicle gets the same default setup.
- **Extensibility**: new vehicle types can be added by extending the registry.
- **Testability**: construction is easy to mock or replace.

## Relationship to SOLID

This factory supports Open/Closed Principle by allowing new vehicle types to be added without changing the main simulation code.

## Example

```python
vehicle = VehicleFactory.create_vehicle("car")
```

## Conclusion

FlowSync uses the Factory Pattern to keep vehicle creation centralized, predictable, and easy to extend as the simulation grows.
