"""Thread-safe industrial state and gradual normal simulation."""
from __future__ import annotations

import random
import threading
from dataclasses import dataclass

from .register_map import MAX_ADDRESS, encode_value


@dataclass
class IndustrialValues:
    temperature: float = 45.0
    pressure: float = 5.5
    vibration: float = 1.3
    motor_speed: int = 1350
    production: int = 0
    motor_command: int = 1
    fault: int = 0


class IndustrialSimulator:
    """Generate gradual, bounded industrial machine values."""

    def __init__(self, seed: int | None = None) -> None:
        self.random = random.Random(seed)
        self.values = IndustrialValues()
        self._lock = threading.Lock()

    def step(self) -> IndustrialValues:
        """Advance normal state by one update tick."""
        with self._lock:
            v = self.values
            v.temperature = _bounded(v.temperature + self.random.uniform(-0.8, 0.8), 35, 65)
            v.pressure = _bounded(v.pressure + self.random.uniform(-0.08, 0.08), 4.5, 6.5)
            v.vibration = _bounded(v.vibration + self.random.uniform(-0.08, 0.08), 0.5, 2.5)
            if v.motor_command and not v.fault:
                v.motor_speed = round(_bounded(v.motor_speed + self.random.randint(-25, 25),
                                               1200, 1500))
                v.production += self.random.randint(1, 3)
            else:
                v.motor_speed = 0
            return IndustrialValues(**vars(v))

    def raw_registers(self) -> list[int]:
        """Return a full raw holding-register image."""
        with self._lock:
            v = self.values
            result = [0] * (MAX_ADDRESS + 1)
            for address, value in ((0, v.temperature), (1, v.pressure),
                                   (2, v.vibration), (3, v.motor_speed),
                                   (4, v.production), (10, v.motor_command),
                                   (11, v.fault)):
                result[address] = encode_value(address, value)
            return result


def _bounded(value: float, low: float, high: float) -> float:
    return max(0.0, min(high, max(low, value)))
