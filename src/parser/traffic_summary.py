"""Traffic summary calculation and terminal rendering."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Iterable


def build_summary(events: Iterable[dict[str, Any]], *, pcap_file: str,
                  scenario: str, total_tcp_packets: int = 0,
                  malformed_or_skipped: int = 0) -> dict[str, Any]:
    """Calculate required per-capture traffic statistics."""
    rows = list(events)
    timestamps = [row["timestamp"] for row in rows]
    start, end = (min(timestamps), max(timestamps)) if timestamps else (None, None)
    duration = 0.0
    if start and end:
        duration = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
    function_codes = Counter(str(row["function_code"]) for row in rows)
    function_names = Counter(row["function_name"] for row in rows)
    registers = Counter(name for row in rows for name in row.get("register_names", []))
    most_common = registers.most_common(1)
    return {
        "pcap_file": pcap_file, "scenario": scenario,
        "capture_start_time": start, "capture_end_time": end,
        "duration_seconds": duration, "total_tcp_packets_inspected": total_tcp_packets,
        "total_modbus_events": len(rows),
        "total_requests": sum(bool(row["is_request"]) for row in rows),
        "total_responses": sum(bool(row["is_response"]) for row in rows),
        "total_exceptions": sum(bool(row["is_exception"]) for row in rows),
        "total_malformed_or_skipped_packets": malformed_or_skipped,
        "source_ip_addresses": sorted({row["source_ip"] for row in rows}),
        "destination_ip_addresses": sorted({row["destination_ip"] for row in rows}),
        "source_ports": sorted({row["source_port"] for row in rows}),
        "destination_ports": sorted({row["destination_port"] for row in rows}),
        "function_code_counts": dict(function_codes),
        "function_name_counts": dict(function_names),
        "read_operation_count": sum(row["operation"] == "read" for row in rows),
        "write_operation_count": sum(row["operation"] == "write" for row in rows),
        "register_usage_counts": dict(registers),
        "most_frequently_accessed_register": most_common[0][0] if most_common else None,
        "transaction_id_count": len({row["transaction_id"] for row in rows}),
        "unit_ids_observed": sorted({row["unit_id"] for row in rows}),
    }


def format_summary(summary: dict[str, Any]) -> str:
    """Render key statistics for a terminal."""
    return (
        f"PCAP: {summary['pcap_file']}\n"
        f"Scenario: {summary['scenario']}\n"
        f"Duration: {summary['duration_seconds']:.3f}s\n"
        f"TCP inspected: {summary['total_tcp_packets_inspected']}\n"
        f"Modbus events: {summary['total_modbus_events']} "
        f"(requests={summary['total_requests']}, responses={summary['total_responses']}, "
        f"exceptions={summary['total_exceptions']})\n"
        f"Malformed/skipped: {summary['total_malformed_or_skipped_packets']}\n"
        f"Functions: {summary['function_name_counts']}\n"
        f"Registers: {summary['register_usage_counts']}"
    )
