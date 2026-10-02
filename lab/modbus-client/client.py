import time
from pymodbus.client import ModbusTcpClient


SERVER_IP = "127.0.0.1"
SERVER_PORT = 5020


def read_registers():
    client = ModbusTcpClient(SERVER_IP, port=SERVER_PORT)

    if not client.connect():
        print("[CLIENT] Unable to connect to Modbus server")
        return

    print("[CLIENT] Connected to Modbus server")

    try:
        while True:
            result = client.read_holding_registers(address=0, count=6, slave=1)

            if result.isError():
                print("[CLIENT] Error while reading registers")
            else:
                values = result.registers

                temperature = values[0]
                pressure = values[1]
                vibration = values[2]
                motor_state = values[3]
                fault_status = values[4]
                production_status = values[5]

                print("\n[CLIENT] Industrial values received:")
                print(f"Temperature       : {temperature} °C")
                print(f"Pressure          : {pressure} bar")
                print(f"Vibration         : {vibration}")
                print(f"Motor State       : {'ON' if motor_state == 1 else 'OFF'}")
                print(f"Fault Status      : {'FAULT' if fault_status == 1 else 'NO_FAULT'}")
                print(f"Production Status : {'RUNNING' if production_status == 1 else 'STOPPED'}")

            time.sleep(3)

    except KeyboardInterrupt:
        print("\n[CLIENT] Stopped by user")

    finally:
        client.close()


if __name__ == "__main__":
    read_registers()