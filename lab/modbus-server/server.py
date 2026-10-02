import random
import time
import threading

from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext, ModbusSequentialDataBlock


# Holding registers:
# address 0 = 40001 = temperature
# address 1 = 40002 = pressure
# address 2 = 40003 = vibration
# address 3 = 40004 = motor_state
# address 4 = 40005 = fault_status
# address 5 = 40006 = production_status

store = ModbusSlaveContext(
    hr=ModbusSequentialDataBlock(0, [0] * 100)
)

context = ModbusServerContext(slaves=store, single=True)


def update_sensor_values():
    """
    This function simulates normal industrial sensor values.
    It updates Modbus holding registers every 2 seconds.
    """
    while True:
        temperature = random.randint(25, 45)
        pressure = random.randint(2, 6)
        vibration = random.randint(10, 40)
        motor_state = 1
        fault_status = 0
        production_status = 1

        store.setValues(3, 0, [
            temperature,
            pressure,
            vibration,
            motor_state,
            fault_status,
            production_status
        ])

        print(
            f"[SERVER] Updated values | "
            f"Temp={temperature}°C | "
            f"Pressure={pressure} bar | "
            f"Vibration={vibration} | "
            f"Motor=ON | Fault=NO | Production=RUNNING"
        )

        time.sleep(2)


if __name__ == "__main__":
    print("[SERVER] Starting Modbus TCP Server on 127.0.0.1:5020")

    sensor_thread = threading.Thread(target=update_sensor_values, daemon=True)
    sensor_thread.start()

    StartTcpServer(context=context, address=("127.0.0.1", 5020))