"""Main simulation controller orchestrating the traffic simulation."""

from core.traffic_manager import TrafficManager
from rendering.renderer import Renderer
import time


class SimulationController:
    """Orchestrates the main simulation loop and coordinates components."""

    def __init__(self, dt=0.1, max_steps=None, debug=False):
        """Initialize simulation controller with traffic manager and renderer.
        
        Args:
            dt: Time step in seconds (default: 0.1)
            max_steps: Maximum number of steps to run (None = continuous)
            debug: Enable debug logging (default: False)
        """
        self.traffic_manager = TrafficManager()
        self.renderer = Renderer()
        self.dt = dt
        self.max_steps = max_steps
        self.debug = debug
        self.running = True
        self.current_step = 0

    def run(self, steps=None, dt=None):
        """Run simulation loop.
        
        Args:
            steps: Number of steps to run. If None, use max_steps from init.
            dt: Time step override. If None, use dt from init.
        """
        if dt is not None:
            self.dt = dt
        
        if steps is not None:
            self.max_steps = steps
        
        self._print_simulation_start()
        
        while self.running:
            self.current_step += 1
            self.update(self.dt)
            
            if self.max_steps is not None and self.current_step >= self.max_steps:
                self.running = False
            
            time.sleep(self.dt)  # Control CPU usage
        
        self._print_simulation_end()

    def update(self, dt):
        """Update simulation state and render.
        
        Args:
            dt: Time step in seconds
        """
        # Update traffic simulation
        self.traffic_manager.update(dt)
        
        # Render current state
        if self.renderer is not None:
            roads = self.traffic_manager.roads
            vehicles = self.traffic_manager.vehicles
            signals = self.traffic_manager.signals
            self.renderer.draw(roads, vehicles, signals)
        
        # Debug logging (light)
        if self.debug and self.current_step % 10 == 0:
            self._print_simulation_state()

    def reset(self):
        """Reset simulation to initial state."""
        self.traffic_manager = TrafficManager()
        self.current_step = 0
        self.running = True

    def _print_simulation_start(self):
        """Print simulation start message."""
        if self.debug:
            print(f"[SIM START] dt={self.dt}, max_steps={self.max_steps}")

    def _print_simulation_end(self):
        """Print simulation end message."""
        if self.debug:
            print(f"[SIM END] Completed {self.current_step} steps")

    def _print_simulation_state(self):
        """Print current simulation state (light debug info)."""
        if not self.debug:
            return
        
        num_vehicles = len(self.traffic_manager.vehicles)
        num_roads = len(self.traffic_manager.roads)
        num_signals = len(self.traffic_manager.signals)
        
        # Get signal states
        signal_states = []
        for signal in self.traffic_manager.signals:
            signal_states.append(f"Signal {signal.id}:{signal.state}")
        signal_str = ", ".join(signal_states) if signal_states else "None"
        
        print(f"[Step {self.current_step}] Vehicles: {num_vehicles}, "
              f"Roads: {num_roads}, Signals: {signal_str}")
