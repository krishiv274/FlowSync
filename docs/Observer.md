# Observer Pattern - Traffic Simulation System

## Overview

The Observer Pattern lets one object publish changes to many dependents without hard-coding those dependents into the subject.

In FlowSync, traffic signals notify vehicles when the signal state changes, which lets vehicles react without polling.

## Where It Is Used

The current observer flow is:

- `TrafficSignal` as the subject
- `Vehicle` as the observer

## What Problem It Solves

Vehicles need to react to signal state changes such as RED, GREEN, and YELLOW, but the design should avoid:

- constant polling of signal state
- direct coupling between signals and concrete vehicle classes
- manual synchronization logic in the simulation loop

## Implementation

### Subject: `TrafficSignal`

`TrafficSignal` maintains a list of registered observers and notifies them when the state changes.

It exposes:

- `attach(vehicle)`
- `detach(vehicle)`
- `notify()`

The signal also acts as a small state machine with timed transitions.

### Observer: `Vehicle`

Vehicles receive updates through:

- `on_signal_change(state)`

The signal state is stored on the vehicle and is then used by the braking logic during `Vehicle.update()`.

## Interaction Flow

1. `TrafficManager` attaches vehicles to a signal.
2. `TrafficSignal.update(dt)` advances the timer.
3. When the timer expires, the signal changes state.
4. `TrafficSignal.notify()` calls `on_signal_change()` on each observer.
5. Vehicles store the new state and use it during the next update.

## Relationship to the Simulation Loop

The update order matters:

1. intersections update first
2. signals update inside intersections
3. roads and lanes update after signal changes
4. vehicles read the latest signal state during movement and braking

That order keeps signal-aware driving behavior consistent.

## Benefits

- **Loose Coupling**: signal logic does not depend on a specific vehicle implementation.
- **Scalability**: many vehicles can listen to one signal.
- **Responsiveness**: vehicles receive state changes immediately.
- **Testability**: observer notifications are easy to verify in isolation.

## Example

```python
signal.attach(vehicle)
signal.notify()
```

## Notes

This implementation uses a lightweight observer protocol rather than a heavyweight event bus. That keeps the design simple and easy to reason about.

## Conclusion

FlowSync uses the Observer Pattern to keep signal-to-vehicle communication direct, modular, and responsive.
