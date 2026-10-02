"""Progressive offline PCAP/PCAPNG reader based on dpkt."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import socket

import dpkt

from src.common.models import TcpPayload


class PcapReadError(RuntimeError):
    """Raised when a capture cannot be read."""


class PcapReader:
    """Iterate relevant TCP payloads without loading the entire PCAP."""

    def __init__(self, path: Path | str, server_port: int = 1502) -> None:
        self.path = Path(path)
        self.server_port = server_port
        self.total_tcp_packets = 0
        self.skipped_packets = 0

    def __iter__(self) -> Iterator[TcpPayload]:
        if not self.path.exists():
            raise PcapReadError(f"PCAP does not exist: {self.path}")
        if not self.path.is_file():
            raise PcapReadError(f"PCAP path is not a file: {self.path}")
        if self.path.stat().st_size == 0:
            raise PcapReadError(f"PCAP is empty: {self.path}")
        try:
            with self.path.open("rb") as stream:
                try:
                    reader = dpkt.pcap.Reader(stream)
                except (ValueError, dpkt.dpkt.NeedData):
                    stream.seek(0)
                    reader = dpkt.pcapng.Reader(stream)
                for timestamp, frame in reader:
                    try:
                        ethernet = dpkt.ethernet.Ethernet(frame)
                        ip = ethernet.data
                        if not isinstance(ip, (dpkt.ip.IP, dpkt.ip6.IP6)):
                            self.skipped_packets += 1
                            continue
                        tcp = ip.data
                        if not isinstance(tcp, dpkt.tcp.TCP):
                            continue
                    except (dpkt.dpkt.UnpackError, ValueError):
                        self.skipped_packets += 1
                        continue
                    self.total_tcp_packets += 1
                    if self.server_port not in (int(tcp.sport), int(tcp.dport)):
                        continue
                    payload = bytes(tcp.data)
                    if not payload:
                        self.skipped_packets += 1
                        continue
                    family = socket.AF_INET6 if isinstance(ip, dpkt.ip6.IP6) else socket.AF_INET
                    src = socket.inet_ntop(family, ip.src)
                    dst = socket.inet_ntop(family, ip.dst)
                    yield TcpPayload(float(timestamp), src, dst, int(tcp.sport),
                                     int(tcp.dport), payload)
        except (dpkt.dpkt.UnpackError, ValueError, OSError, EOFError) as exc:
            raise PcapReadError(f"Unable to read PCAP {self.path}: {exc}") from exc
