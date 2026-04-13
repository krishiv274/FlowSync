"""Renderer for traffic simulation visualization."""


class Renderer:
    """Handles rendering of simulation entities."""

    def __init__(self):
        """Initialize the renderer."""
        # Placeholder for future rendering setup (e.g., pygame screen)
        self.frame_count = 0

    def draw(self, roads, vehicles, signals):
        """Draw the traffic simulation.
        
        Args:
            roads: List of Road objects
            vehicles: List of Vehicle objects
            signals: List of TrafficSignal objects
        """
        # Increment frame count
        self.frame_count += 1

        # Basic console rendering for debugging
        print(f"\n--- Frame {self.frame_count} ---")

        # Print roads
        print(f"Roads: {len(roads)}")

        # Print vehicles with positions if available
        print("Vehicles:")
        for v in vehicles:
            pos = getattr(v, "position", None)
            vel = getattr(v, "velocity", None)
            print(f"  Vehicle id={id(v)} pos={pos} vel={vel}")

        # Print signals with state if available
        print("Signals:")
        for s in signals:
            state = getattr(s, "state", None)
            print(f"  Signal id={id(s)} state={state}")

        # NOTE: This is a placeholder renderer.
        # Replace with pygame or graphical rendering later.
