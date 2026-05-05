import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from physics.interfaces.braking_strategy import IBrakingStrategy
from physics.interfaces.physics_model import IPhysicsModel


class DummyPhysicsModel(IPhysicsModel):
    def compute_acceleration(self, vehicle, lead_vehicle):
        return 1.5


class DummyBrakingStrategy(IBrakingStrategy):
    def should_brake(self, vehicle, environment):
        return environment.get('must_brake', False)


class DummyVehicle:
    pass


def test_physics_model_is_abstract_and_snake_case_works():
    try:
        IPhysicsModel()
        raise AssertionError('IPhysicsModel should not be instantiable')
    except TypeError:
        pass

    model = DummyPhysicsModel()
    vehicle = DummyVehicle()

    assert model.compute_acceleration(vehicle, None) == 1.5


def test_braking_strategy_is_abstract_and_snake_case_works():
    try:
        IBrakingStrategy()
        raise AssertionError('IBrakingStrategy should not be instantiable')
    except TypeError:
        pass

    strategy = DummyBrakingStrategy()
    vehicle = DummyVehicle()

    assert strategy.should_brake(vehicle, {'must_brake': True}) is True


def run_with_logs() -> None:
    tests = [
        test_physics_model_is_abstract_and_snake_case_works,
        test_braking_strategy_is_abstract_and_snake_case_works,
    ]

    print('Running interface tests...')
    for test_func in tests:
        test_func()
        print(f'PASS: {test_func.__name__}')
    print('All interface tests passed.')


if __name__ == '__main__':
    run_with_logs()
