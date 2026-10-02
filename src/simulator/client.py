"""CLI Modbus/TCP client and scenario entry point."""
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from pymodbus.client import ModbusTcpClient

from src.common.config import load_config
from src.common.logging_config import configure_logging
from src.simulator.register_map import MAX_ADDRESS, decode_range, encode_value


class IndustrialClient:
    """Resilient wrapper around the synchronous pymodbus TCP client."""

    def __init__(self, host: str, port: int, unit_id: int = 1,
                 retries: int = 10, retry_delay: float = 2,
                 logger: logging.Logger | None = None) -> None:
        self.unit_id = unit_id
        self.retries = retries
        self.retry_delay = retry_delay
        self.client = ModbusTcpClient(host, port=port, timeout=3)
        self.logger = logger or logging.getLogger(__name__)

    def connect(self) -> bool:
        """Connect with bounded retries."""
        for attempt in range(1, self.retries + 1):
            if self.client.connect():
                self.logger.info("Connected to Modbus server")
                return True
            self.logger.warning("Connection attempt %d/%d failed", attempt, self.retries)
            if attempt < self.retries:
                time.sleep(self.retry_delay)
        return False

    def read(self, address: int = 0, count: int = MAX_ADDRESS + 1) -> list[int] | None:
        """Read holding registers, returning None on protocol/transport error."""
        try:
            response = self.client.read_holding_registers(
                address, count=count, device_id=self.unit_id)
            if response.isError():
                self.logger.error("Modbus read error: %s", response)
                return None
            return list(response.registers)
        except Exception as exc:  # network errors must not kill a scenario
            self.logger.error("Read failed: %s", exc)
            return None

    def write(self, address: int, physical_value: float | int) -> bool:
        """Write one mapped register, logging every attempted write."""
        raw = encode_value(address, physical_value)
        self.logger.warning("WRITE address=%d value=%s raw=%d", address, physical_value, raw)
        try:
            response = self.client.write_register(
                address, raw, device_id=self.unit_id)
            if response.isError():
                self.logger.error("Modbus write error: %s", response)
                return False
            return True
        except Exception as exc:
            self.logger.error("Write failed: %s", exc)
            return False

    def close(self) -> None:
        """Close the underlying socket."""
        self.client.close()


def format_values(start: int, values: list[int]) -> str:
    """Format decoded mapped values in one readable line."""
    return " | ".join(f"{item['name']}={item['value']} {item['unit']}"
                      for item in decode_range(start, values))


def main() -> None:
    """Parse CLI arguments and dispatch a scenario."""
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("normal", "rapid_polling",
                        "sensitive_write", "dangerous_values"), default="normal")
    parser.add_argument("--duration", type=float, default=60)
    parser.add_argument("--interval", type=float,
                        default=config["modbus"]["client_poll_interval_seconds"])
    parser.add_argument("--host", default=config["modbus"]["host"])
    parser.add_argument("--port", type=int, default=config["modbus"]["port"])
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output-log", type=Path)
    args = parser.parse_args()
    from src.simulator.scenarios import run_scenario
    run_scenario(**vars(args))


if __name__ == "__main__":
    main()
