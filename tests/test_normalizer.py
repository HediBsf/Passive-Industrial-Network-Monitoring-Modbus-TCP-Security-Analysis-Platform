import json
import socket

import dpkt

from src.parser.normalizer import normalize_pcap


def adu(tid: int, pdu: bytes) -> bytes:
    return tid.to_bytes(2, "big") + b"\x00\x00" + (len(pdu) + 1).to_bytes(2, "big") + b"\x01" + pdu


def make_pcap(path):
    def frame(sport, dport, payload):
        tcp = dpkt.tcp.TCP(sport=sport, dport=dport, flags=dpkt.tcp.TH_ACK, data=payload)
        ip = dpkt.ip.IP(src=socket.inet_aton("127.0.0.1"),
                        dst=socket.inet_aton("127.0.0.1"), p=dpkt.ip.IP_PROTO_TCP,
                        data=tcp)
        ip.len = len(ip)
        return bytes(dpkt.ethernet.Ethernet(
            src=b"\x00\x01\x02\x03\x04\x05", dst=b"\x06\x07\x08\x09\x0a\x0b",
            type=dpkt.ethernet.ETH_TYPE_IP, data=ip))
    with path.open("wb") as stream:
        writer = dpkt.pcap.Writer(stream)
        writer.writepkt(frame(41000, 1502, adu(4, b"\x03\x00\x00\x00\x03")), ts=1)
        writer.writepkt(frame(1502, 41000, adu(4, b"\x03\x06\x01\xa9\x02\x0d\x00\xaf")), ts=2)
        writer.close()


def test_normalization_schema_and_summary(tmp_path):
    pcap = tmp_path / "normal_fixture.pcap"
    make_pcap(pcap)
    outputs = normalize_pcap(pcap, tmp_path / "out")
    rows = [json.loads(line) for line in outputs["jsonl"].read_text(encoding="utf-8").splitlines()]
    summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
    assert len(rows) == 2
    assert rows[0]["schema_version"] == "1.0"
    assert rows[1]["decoded_values"][0]["name"] == "temperature"
    assert summary["total_modbus_events"] == 2
    assert summary["total_requests"] == summary["total_responses"] == 1
    assert summary["register_usage_counts"]["temperature"] == 2


def test_no_overwrite_without_flag(tmp_path):
    pcap = tmp_path / "normal_fixture.pcap"
    make_pcap(pcap)
    normalize_pcap(pcap, tmp_path / "out")
    try:
        normalize_pcap(pcap, tmp_path / "out")
        assert False, "expected FileExistsError"
    except FileExistsError:
        pass
