"""Traffic-generation scenarios. No detection logic belongs here."""
from __future__ import annotations

import random
import time
from pathlib import Path

from src.common.config import load_config
from src.common.logging_config import configure_logging
from src.simulator.client import IndustrialClient, format_values


def run_scenario(scenario: str = "normal", duration: float = 60,
                 interval: float = 1, host: str = "127.0.0.1", port: int = 1502,
                 seed: int | None = None, output_log: Path | None = None) -> bool:
    """Run a named scenario against the explicitly local simulator."""
    if duration <= 0 or interval <= 0:
        raise ValueError("duration and interval must be positive")
    # "modbus-server" is the fixed Docker Compose service on the private lab network.
    if host not in {"127.0.0.1", "localhost", "::1", "modbus-server"}:
        raise ValueError("Safety guard: scenarios may target only the local simulator")
    config = load_config()
    logger = configure_logging(f"scenario_{scenario}", config["logging"]["level"],
                               config["logging"]["directory"], output_log)
    client = IndustrialClient(host, port, config["modbus"]["unit_id"],
                              config["modbus"]["connection_retries"],
                              config["modbus"]["retry_delay_seconds"], logger)
    if not client.connect():
        logger.error("Unable to connect")
        return False
    deadline = time.monotonic() + duration
    rng = random.Random(seed)
    logger.info("Starting scenario=%s duration=%.2fs interval=%.3fs",
                scenario, duration, interval)
    try:
        if scenario == "normal":
            client.write(10, 1)
            client.write(11, 0)
            while time.monotonic() < deadline:
                values = client.read()
                if values is not None:
                    logger.info(format_values(0, values))
                time.sleep(interval)
        elif scenario == "rapid_polling":
            rapid_interval = min(interval, 0.05)
            while time.monotonic() < deadline:
                client.read(0, 1)
                time.sleep(rapid_interval)
        elif scenario == "sensitive_write":
            state = 0
            while time.monotonic() < deadline:
                client.write(10, state)
                if rng.random() < 0.25:
                    client.write(11, 1)
                state = 1 - state
                time.sleep(interval)
        elif scenario == "dangerous_values":
            while time.monotonic() < deadline:
                client.write(0, 85.0)
                client.write(1, 9.0)
                client.write(2, 8.0)
                time.sleep(interval)
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
        return True
    except KeyboardInterrupt:
        logger.info("Scenario interrupted")
        return False
    finally:
        if scenario in {"sensitive_write", "dangerous_values"}:
            logger.info("Restoring safe values")
            client.write(10, 1)
            client.write(11, 0)
            if scenario == "dangerous_values":
                client.write(0, 45.0)
                client.write(1, 5.5)
                client.write(2, 1.3)
        client.close()
        logger.info("Scenario finished")
