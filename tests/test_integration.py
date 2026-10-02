import socket
import subprocess
import sys
import time

import pytest
from pymodbus.client import ModbusTcpClient


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.mark.integration
def test_server_client_read_write():
    port = free_port()
    process = subprocess.Popen(
        [sys.executable, "-m", "src.simulator.server", "--port", str(port),
         "--interval", "0.1", "--seed", "3"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    client = ModbusTcpClient("127.0.0.1", port=port, timeout=1)
    try:
        for _ in range(30):
            if client.connect():
                break
            time.sleep(0.1)
        else:
            pytest.fail("server did not start")
        result = client.read_holding_registers(0, count=12, device_id=1)
        assert not result.isError() and 350 <= result.registers[0] <= 650
        written = client.write_register(10, 0, device_id=1)
        assert not written.isError()
        time.sleep(0.25)
        speed = client.read_holding_registers(3, count=1, device_id=1)
        assert speed.registers[0] == 0
    finally:
        client.close()
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
