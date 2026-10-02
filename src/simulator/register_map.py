"""Single authoritative industrial holding-register map."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RegisterDefinition:
    address: int
    name: str
    unit: str
    scale: int = 1
    writable: bool = False
    values: dict[int, str] | None = None

    def encode(self, physical_value: float | int) -> int:
        raw = round(float(physical_value) * self.scale)
        if not 0 <= raw <= 65535:
            raise ValueError(f"{self.name} encodes outside uint16: {raw}")
        return raw

    def decode(self, raw_value: int) -> float | int:
        return raw_value if self.scale == 1 else raw_value / self.scale


REGISTERS: dict[int, RegisterDefinition] = {
    0: RegisterDefinition(0, "temperature", "°C", 10),
    1: RegisterDefinition(1, "pressure", "bar", 100),
    2: RegisterDefinition(2, "vibration", "mm/s", 100),
    3: RegisterDefinition(3, "motor_speed", "RPM"),
    4: RegisterDefinition(4, "production", "units"),
    10: RegisterDefinition(10, "motor_command", "state", writable=True,
                           values={0: "stopped", 1: "running"}),
    11: RegisterDefinition(11, "fault", "state", writable=True,
                           values={0: "no fault", 1: "fault"}),
}
MAX_ADDRESS = max(REGISTERS)


def get_register(address: int) -> RegisterDefinition | None:
    """Return a mapped register definition, if any."""
    return REGISTERS.get(address)


def encode_value(address: int, value: float | int) -> int:
    """Encode a physical value for a mapped register."""
    definition = get_register(address)
    if definition is None:
        raise KeyError(f"Unknown register address: {address}")
    return definition.encode(value)


def decode_value(address: int, raw_value: int) -> float | int:
    """Decode a raw uint16 value for a mapped register."""
    definition = get_register(address)
    if definition is None:
        raise KeyError(f"Unknown register address: {address}")
    return definition.decode(raw_value)


def decode_range(start: int, values: list[int]) -> list[dict[str, Any]]:
    """Decode mapped values in a contiguous register range."""
    decoded: list[dict[str, Any]] = []
    for offset, raw in enumerate(values):
        address = start + offset
        definition = get_register(address)
        if definition:
            decoded.append({"address": address, "name": definition.name,
                            "unit": definition.unit, "raw": raw,
                            "value": definition.decode(raw)})
    return decoded


def display_register_map() -> str:
    """Render the register map as readable lines."""
    return "\n".join(
        f"  HR {r.address:>2}: {r.name:<14} unit={r.unit:<6} scale={r.scale}"
        for r in REGISTERS.values()
    )
