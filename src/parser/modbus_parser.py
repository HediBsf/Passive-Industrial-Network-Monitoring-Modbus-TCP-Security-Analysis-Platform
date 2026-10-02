"""Manual Modbus Application Protocol header and PDU decoder."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common.models import ModbusEvent, TcpPayload
from src.simulator.register_map import decode_range, get_register

FUNCTIONS = {
    3: ("Read Holding Registers", "read"),
    6: ("Write Single Register", "write"),
    16: ("Write Multiple Registers", "write"),
}


class ModbusParseError(ValueError):
    """Raised for incomplete or invalid Modbus/TCP payloads."""


class ModbusParser:
    """Stateful decoder that correlates read responses by transaction ID."""

    def __init__(self, server_port: int = 1502, scenario: str | None = None,
                 pcap_file: str | None = None, schema_version: str = "1.0") -> None:
        self.server_port = server_port
        self.scenario = scenario
        self.pcap_file = pcap_file
        self.schema_version = schema_version
        self.pending: dict[tuple[int, int], tuple[int, int]] = {}
        self.malformed = 0

    def parse(self, packet: TcpPayload) -> ModbusEvent | None:
        """Parse one complete Modbus/TCP ADU, counting malformed payloads."""
        try:
            return self._parse(packet)
        except (ModbusParseError, IndexError, ValueError):
            self.malformed += 1
            return None

    def _parse(self, packet: TcpPayload) -> ModbusEvent:
        data = packet.payload
        if len(data) < 8:
            raise ModbusParseError("Payload shorter than MBAP header and function code")
        transaction_id = int.from_bytes(data[0:2], "big")
        protocol_id = int.from_bytes(data[2:4], "big")
        length = int.from_bytes(data[4:6], "big")
        if protocol_id != 0 or length < 2 or len(data) < 6 + length:
            raise ModbusParseError("Invalid MBAP protocol, length, or truncated ADU")
        unit_id = data[6]
        pdu = data[7:6 + length]
        wire_fc = pdu[0]
        is_exception = bool(wire_fc & 0x80)
        function_code = wire_fc & 0x7F
        function_name, operation = FUNCTIONS.get(
            function_code, (f"Function {function_code}", "unknown"))
        is_request = packet.destination_port == self.server_port
        is_response = packet.source_port == self.server_port
        direction = "client_to_server" if is_request else "server_to_client"
        address: int | None = None
        quantity: int | None = None
        raw_values: list[int] | None = None
        decoded: list[dict[str, Any]] | None = None
        exception_code = pdu[1] if is_exception and len(pdu) >= 2 else None

        if is_exception:
            if len(pdu) < 2:
                raise ModbusParseError("Truncated exception response")
        elif function_code == 3:
            if is_request:
                _require(pdu, 5)
                address = int.from_bytes(pdu[1:3], "big")
                quantity = int.from_bytes(pdu[3:5], "big")
                if not 1 <= quantity <= 125:
                    raise ModbusParseError("Invalid read quantity")
                self.pending[(transaction_id, unit_id)] = (address, quantity)
            else:
                _require(pdu, 2)
                byte_count = pdu[1]
                if byte_count % 2 or len(pdu) < 2 + byte_count:
                    raise ModbusParseError("Invalid read response byte count")
                raw_values = [int.from_bytes(pdu[i:i + 2], "big")
                              for i in range(2, 2 + byte_count, 2)]
                quantity = len(raw_values)
                request = self.pending.pop((transaction_id, unit_id), None)
                if request:
                    address = request[0]
                    decoded = decode_range(address, raw_values)
        elif function_code == 6:
            _require(pdu, 5)
            address = int.from_bytes(pdu[1:3], "big")
            raw_values = [int.from_bytes(pdu[3:5], "big")]
            quantity = 1
            decoded = decode_range(address, raw_values)
        elif function_code == 16:
            _require(pdu, 5)
            address = int.from_bytes(pdu[1:3], "big")
            quantity = int.from_bytes(pdu[3:5], "big")
            if is_request:
                _require(pdu, 6)
                byte_count = pdu[5]
                if byte_count != quantity * 2 or len(pdu) < 6 + byte_count:
                    raise ModbusParseError("Invalid multiple-write byte count")
                raw_values = [int.from_bytes(pdu[i:i + 2], "big")
                              for i in range(6, 6 + byte_count, 2)]
                decoded = decode_range(address, raw_values)
        register_names = []
        if address is not None:
            for item_address in range(address, address + (quantity or 1)):
                definition = get_register(item_address)
                if definition:
                    register_names.append(definition.name)
        return ModbusEvent(
            timestamp=datetime.fromtimestamp(packet.timestamp, timezone.utc).isoformat(),
            source_ip=packet.source_ip, destination_ip=packet.destination_ip,
            source_port=packet.source_port, destination_port=packet.destination_port,
            direction=direction, transaction_id=transaction_id,
            protocol_id=protocol_id, length=length, unit_id=unit_id,
            function_code=function_code, function_name=function_name,
            operation=operation, register_address=address, quantity=quantity,
            raw_values=raw_values, decoded_values=decoded,
            is_request=is_request, is_response=is_response,
            is_exception=is_exception, exception_code=exception_code,
            raw_payload_hex=data[:6 + length].hex(), scenario=self.scenario,
            pcap_file=self.pcap_file, schema_version=self.schema_version,
            register_names=register_names)


def _require(data: bytes, size: int) -> None:
    if len(data) < size:
        raise ModbusParseError(f"Truncated PDU: expected at least {size} bytes")


def detect_scenario(path: Path | str) -> str:
    """Infer a known scenario from a filename or parent path."""
    text = str(path).lower()
    for name in ("rapid_polling", "sensitive_write", "dangerous_values", "normal"):
        if name in text:
            return name
    return "unknown"


def parse_payload(payload: bytes, *, source_port: int = 50000,
                  destination_port: int = 1502, timestamp: float = 0,
                  parser: ModbusParser | None = None) -> ModbusEvent | None:
    """Convenience helper used by tests and integrations."""
    decoder = parser or ModbusParser()
    return decoder.parse(TcpPayload(timestamp, "127.0.0.1", "127.0.0.1",
                                    source_port, destination_port, payload))
