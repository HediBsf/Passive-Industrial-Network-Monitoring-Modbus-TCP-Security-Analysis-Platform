import time
from pymodbus.client import ModbusTcpClient


SERVER_IP = "127.0.0.1"
SERVER_PORT = 5020


def run_normal_scenario():
    client = ModbusTcpClient(SERVER_IP, port=SERVER_PORT)

    if not client.connect():
        print("[SCENARIO] Unable to connect to Modbus server")
        return

    print("[SCENARIO] Normal scenario started")

    try:
        for i in range(20):
            result = client.read_holding_registers(address=0, count=6, slave=1)

            if not result.isError():
                print(f"[SCENARIO] Normal read {i + 1}: {result.registers}")
            else:
                print("[SCENARIO] Read error")

            time.sleep(2)

    finally:
        client.close()
        print("[SCENARIO] Normal scenario finished")


if __name__ == "__main__":
    run_normal_scenario()