"""Main simulation controller orchestrating the traffic simulation."""

from core.traffic_manager import TrafficManager
from rendering.renderer import Renderer
import time


class SimulationController:
    """Orchestrates the main simulation loop and coordinates components."""

    def __init__(self):
        """Initialize simulation controller with traffic manager and renderer."""
        self.traffic_manager = TrafficManager()
        self.renderer = Renderer()
        self.running = True
        self.dt = 0.1
        self.max_steps = None  # Optional limit for testing loops

    def run(self):
        """Main simulation loop."""
        steps = 0
        while self.running:
            self.update(self.dt)
            steps += 1
            if self.max_steps is not None and steps >= self.max_steps:
                self.running = False
            time.sleep(self.dt)  # crude time control to prevent CPU overuse

    def update(self, dt):
        """Update simulation state and render.
        
        Args:
            dt: Time step in seconds
        """
        # Update traffic simulation
        self.traffic_manager.update(dt)
        
        # Basic safety: skip rendering if renderer is not initialized
        if self.renderer is None:
            return
        
        # Render current state
        roads = self.traffic_manager.roads
        vehicles = self.traffic_manager.vehicles
        signals = self.traffic_manager.signals
        
        self.renderer.draw(roads, vehicles, signals)

    def reset(self):
        """Reset simulation to initial state."""
        self.traffic_manager = TrafficManager()
        self.running = True
