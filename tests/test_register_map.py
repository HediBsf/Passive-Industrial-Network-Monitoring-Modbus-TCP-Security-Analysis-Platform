import pytest

from src.simulator.datastore import IndustrialSimulator
from src.simulator.register_map import REGISTERS, decode_value, encode_value


@pytest.mark.parametrize(("address", "value"), [(0, 42.5), (1, 5.25), (2, 1.75),
                                                  (3, 1350), (4, 12), (10, 1)])
def test_encode_decode_round_trip(address, value):
    assert decode_value(address, encode_value(address, value)) == value


def test_address_to_name_mapping():
    assert REGISTERS[0].name == "temperature"
    assert REGISTERS[11].name == "fault"


def test_normal_generation_bounds_and_progression():
    simulator = IndustrialSimulator(seed=7)
    previous = simulator.values.temperature
    for _ in range(500):
        values = simulator.step()
        assert 35 <= values.temperature <= 65
        assert 4.5 <= values.pressure <= 6.5
        assert 0.5 <= values.vibration <= 2.5
        assert 1200 <= values.motor_speed <= 1500
        assert abs(values.temperature - previous) <= 0.8 + 1e-9
        previous = values.temperature
