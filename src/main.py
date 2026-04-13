"""Main entry point for FlowSync traffic simulation."""

from core.simulation_controller import SimulationController


def main():
    """Run the traffic simulation."""
    sim = SimulationController()
    sim.run()


if __name__ == "__main__":
    main()