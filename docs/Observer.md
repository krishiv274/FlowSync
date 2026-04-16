# Observer Pattern – Traffic Simulation System

## Overview

The Observer Pattern is a behavioral design pattern where an object (subject) maintains a list of dependents (observers) and notifies them automatically of any state changes.

This pattern is ideal for systems where multiple components need to react to changes in another component without tight coupling.

---

## Where It Is Used

In this project, the Observer Pattern is implemented for:

* **Traffic Signals (Subject)**
* **Vehicles (Observers)**

---

## Problem It Solves

Vehicles need to respond dynamically to traffic signal changes (e.g., RED → GREEN), but:

* Vehicles should not continuously poll signal state
* Traffic signals should not depend on specific vehicle implementations

---

## Implementation

### Subject: TrafficSignal

Responsible for:

* Maintaining a list of subscribed vehicles
* Notifying all vehicles when its state changes

```python
class TrafficSignal:
    def attach(self, vehicle): ...
    def detach(self, vehicle): ...
    def notify(self): ...
```

---

### Observer: Vehicle

Each vehicle:

* Subscribes to nearby traffic signals
* Reacts when notified

```python
class Vehicle:
    def onSignalChange(self, state): ...
```

---

## Interaction Flow

1. Vehicle approaches intersection
2. Vehicle subscribes to TrafficSignal
3. TrafficSignal changes state
4. TrafficSignal calls `notify()`
5. All subscribed vehicles receive update
6. Vehicles adjust behavior (brake/accelerate)

---

## Benefits

* **Loose Coupling**: TrafficSignal and Vehicle are independent
* **Scalability**: Multiple vehicles can subscribe to one signal
* **Real-Time Updates**: Immediate reaction to signal changes
* **Extensibility**: New observer types can be added easily

---

## Example

```python
signal.attach(vehicle)
signal.notify()
```

---

## Conclusion

The Observer Pattern enables efficient and scalable communication between traffic signals and vehicles, ensuring realistic and responsive traffic behavior.
