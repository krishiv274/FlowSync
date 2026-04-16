# Factory Pattern – Traffic Simulation System

## Overview

The Factory Pattern is a creational design pattern that provides an interface for creating objects without specifying their exact class.

It centralizes object creation logic and promotes flexibility and scalability.

---

## Where It Is Used

In this project, the Factory Pattern is used for:

* **Vehicle creation**

---

## Problem It Solves

Different types of vehicles (Car, Truck, Bike) need to be created with:

* Different properties
* Different physics parameters
* Different behaviors

Without a factory:

* Object creation logic would be scattered
* Code would become difficult to maintain

---

## Implementation

### Factory Class: VehicleFactory

Responsible for:

* Creating vehicle instances based on type
* Assigning appropriate configurations

```python
class VehicleFactory:
    def createVehicle(self, type):
        if type == "car":
            return Car()
        elif type == "truck":
            return Truck()
        elif type == "bike":
            return Bike()
```

---

### Product Classes

* `Vehicle` (base class)
* `Car`, `Truck`, `Bike` (derived classes)

---

## Interaction Flow

1. Simulation requests a new vehicle
2. Calls `VehicleFactory.createVehicle(type)`
3. Factory instantiates correct subclass
4. Returns fully initialized object

---

## Benefits

* **Encapsulation**: Object creation logic is centralized
* **Scalability**: New vehicle types can be added easily
* **Maintainability**: Reduces duplication
* **Flexibility**: Client code is independent of concrete classes

---

## Example

```python
factory = VehicleFactory()
vehicle = factory.createVehicle("car")
```

---

## Conclusion

The Factory Pattern simplifies object creation and ensures that the system remains extensible and maintainable as new vehicle types are introduced.
