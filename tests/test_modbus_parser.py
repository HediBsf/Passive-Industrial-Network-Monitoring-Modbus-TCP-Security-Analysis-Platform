from src.common.models import TcpPayload
from src.parser.modbus_parser import ModbusParser, parse_payload


def adu(tid: int, pdu: bytes, unit: int = 1) -> bytes:
    return tid.to_bytes(2, "big") + b"\x00\x00" + (len(pdu) + 1).to_bytes(2, "big") + bytes([unit]) + pdu


def test_read_holding_request():
    event = parse_payload(adu(1, b"\x03\x00\x00\x00\x05"))
    assert event and event.is_request
    assert event.register_address == 0 and event.quantity == 5
    assert event.function_name == "Read Holding Registers"


def test_read_holding_response_correlated_and_decoded():
    parser = ModbusParser()
    parser.parse(TcpPayload(1, "client", "server", 50000, 1502,
                            adu(9, b"\x03\x00\x00\x00\x03")))
    event = parser.parse(TcpPayload(2, "server", "client", 1502, 50000,
                                   adu(9, b"\x03\x06\x01\xa9\x02\x0d\x00\xaf")))
    assert event and event.is_response and event.register_address == 0
    assert event.decoded_values[0]["value"] == 42.5
    assert event.decoded_values[1]["value"] == 5.25


def test_write_single_request():
    event = parse_payload(adu(2, b"\x06\x00\x0a\x00\x01"))
    assert event and event.operation == "write"
    assert event.register_address == 10 and event.raw_values == [1]
    assert event.register_names == ["motor_command"]


def test_exception_response():
    event = parse_payload(adu(3, b"\x83\x02"), source_port=1502,
                          destination_port=50000)
    assert event and event.is_exception and event.exception_code == 2
    assert event.function_code == 3


def test_malformed_payload_is_skipped():
    parser = ModbusParser()
    assert parse_payload(b"\x00\x01", parser=parser) is None
    assert parser.malformed == 1
