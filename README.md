# FlowSync

FlowSync is a Python-based traffic simulation project focused on building a clean, extensible architecture for vehicle behavior, traffic control, and visualization.

## Project Status

This repository is currently in an **early development stage**.

Implemented today:
- Basic Pygame application loop in `main.py`
- Initial package/module structure for simulation, entities, physics, and rendering
- Starter entity implementation in `entities/vehicle.py`

Planned next:
- Real traffic simulation loop
- IDM-based motion and braking strategies
- Signal-aware vehicle behavior and scheduling

## Goals

- Build a modular traffic simulation foundation using clear separation of concerns
- Keep domain components extensible for future models (IDM, lane changing, adaptive control)
- Support experimentation for traffic engineering and autonomous systems scenarios

## Architecture Direction

Target architecture:

```text
SimulationController -> TrafficManager -> Entities -> Physics -> Rendering
```

The repository already contains these modules and interfaces as a scaffold, with implementation to be expanded incrementally.

## Repository Structure

```text
FlowSync/
├── src/
│   ├── assets/
│   ├── core/
│   ├── entities/
│   ├── factory/
│   ├── physics/
│   ├── rendering/
│   ├── simulation/
│   ├── utils/
│   ├── main.py
│   ├── requirements.txt
│   └── settings.py
├── diagrams
├── docs
├── LICENSE
└── README.md
```

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Setup

```bash
git clone https://github.com/krishiv274/FlowSync.git
cd FlowSync
python -m pip install -r src/requirements.txt
```

## Run

```bash
python src/main.py
```

## Roadmap

- Implement traffic manager and simulation controller flow
- Expand vehicle model and IDM integration in `physics/`
- Add traffic signals, lane/intersection logic, and observer-based updates
- Introduce tests and validation scenarios
- Add richer rendering and simulation controls

## Contributing

Contributions are welcome. If you want to help:

1. Open an issue describing the bug or feature proposal.
2. Fork the repository and create a focused branch.
3. Submit a pull request with clear change notes.

## License

This project is licensed under the MIT License.
