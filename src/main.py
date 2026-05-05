"""Main entry point for FlowSync traffic simulation."""

from core.simulation_controller import SimulationController


def main():
    """Run the traffic simulation."""
    # Create simulation controller with:
    # - dt (time step): 0.1 seconds per frame
    # - max_steps: 20 steps for standard validation
    # - debug: False (set to True to enable debug logging)
    sim = SimulationController(dt=0.1, max_steps=20, debug=False)
    
    # Run simulation
    sim.run()


if __name__ == "__main__":
    main()