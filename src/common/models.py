"""Typed parser models."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TcpPayload:
    """TCP payload and addressing metadata extracted from a packet."""
    timestamp: float
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    payload: bytes


@dataclass
class ModbusEvent:
    """Normalized Modbus/TCP request or response."""
    timestamp: str
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    direction: str
    transaction_id: int
    protocol_id: int
    length: int
    unit_id: int
    function_code: int
    function_name: str
    operation: str
    register_address: int | None = None
    quantity: int | None = None
    raw_values: list[int] | None = None
    decoded_values: list[dict[str, Any]] | None = None
    is_request: bool = False
    is_response: bool = False
    is_exception: bool = False
    exception_code: int | None = None
    raw_payload_hex: str = ""
    scenario: str | None = None
    pcap_file: str | None = None
    schema_version: str = "1.0"
    register_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-ready dictionary."""
        return asdict(self)
