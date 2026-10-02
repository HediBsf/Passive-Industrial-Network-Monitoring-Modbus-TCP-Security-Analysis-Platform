"""Configurable local Modbus/TCP industrial machine server."""
from __future__ import annotations

import argparse
import logging
import threading
import time

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import StartTcpServer

from src.common.config import load_config
from src.common.logging_config import configure_logging
from src.simulator.datastore import IndustrialSimulator
from src.simulator.register_map import MAX_ADDRESS, display_register_map


def build_context(simulator: IndustrialSimulator) -> tuple[ModbusServerContext, ModbusDeviceContext]:
    """Build a pymodbus server context backed by holding registers."""
    # DeviceContext translates protocol address 0 to block address 1.
    device = ModbusDeviceContext(
        hr=ModbusSequentialDataBlock(1, simulator.raw_registers())
    )
    return ModbusServerContext(devices=device, single=True), device


def update_loop(simulator: IndustrialSimulator, device: ModbusDeviceContext,
                interval: float, stop: threading.Event, logger: logging.Logger) -> None:
    """Update simulated values until stopped."""
    while not stop.wait(interval):
        values = simulator.step()
        # Preserve commands written by Modbus clients.
        command = device.getValues(3, 10, 1)
        fault = device.getValues(3, 11, 1)
        if isinstance(command, list):
            simulator.values.motor_command = int(command[0])
        if isinstance(fault, list):
            simulator.values.fault = int(fault[0])
        device.setValues(3, 0, simulator.raw_registers())
        logger.debug("Updated machine state: %s", values)


def main() -> None:
    """Run the Modbus server until interrupted."""
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=config["modbus"]["host"])
    parser.add_argument("--port", type=int, default=config["modbus"]["port"])
    parser.add_argument("--interval", type=float,
                        default=config["modbus"]["update_interval_seconds"])
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or args.interval <= 0:
        parser.error("port must be 1..65535 and interval must be positive")
    logger = configure_logging("server", config["logging"]["level"],
                               config["logging"]["directory"])
    simulator = IndustrialSimulator(args.seed)
    context, device = build_context(simulator)
    stop = threading.Event()
    worker = threading.Thread(target=update_loop,
                              args=(simulator, device, args.interval, stop, logger),
                              daemon=True)
    worker.start()
    logger.info("Starting Modbus TCP server at %s:%s\n%s",
                args.host, args.port, display_register_map())
    try:
        StartTcpServer(context=context, address=(args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        stop.set()
        worker.join(timeout=max(2.0, args.interval + 0.5))


if __name__ == "__main__":
    main()
