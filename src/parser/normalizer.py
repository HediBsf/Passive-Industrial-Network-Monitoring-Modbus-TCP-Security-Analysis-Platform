"""Normalize one PCAP or a directory of PCAPs into JSONL, JSON, and summary JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.common.config import load_config
from src.parser.modbus_parser import ModbusParser, detect_scenario
from src.parser.pcap_reader import PcapReadError, PcapReader
from src.parser.traffic_summary import build_summary, format_summary


def normalize_pcap(path: Path | str, output_directory: Path | str = "results/parsed",
                   server_port: int = 1502, schema_version: str = "1.0",
                   overwrite: bool = False) -> dict[str, Path]:
    """Parse and atomically write all three normalized output formats."""
    pcap_path = Path(path)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    targets = {
        "jsonl": output / f"{pcap_path.stem}.jsonl",
        "json": output / f"{pcap_path.stem}.json",
        "summary": output / f"{pcap_path.stem}_summary.json",
    }
    existing = [str(item) for item in targets.values() if item.exists()]
    if existing and not overwrite:
        raise FileExistsError("Refusing to overwrite existing output(s): " + ", ".join(existing))
    scenario = detect_scenario(pcap_path)
    reader = PcapReader(pcap_path, server_port)
    parser = ModbusParser(server_port, scenario, pcap_path.name, schema_version)
    events: list[dict[str, Any]] = []
    for packet in reader:
        event = parser.parse(packet)
        if event:
            events.append(event.to_dict())
    summary = build_summary(events, pcap_file=pcap_path.name, scenario=scenario,
                            total_tcp_packets=reader.total_tcp_packets,
                            malformed_or_skipped=reader.skipped_packets + parser.malformed)
    targets["jsonl"].write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
        encoding="utf-8")
    targets["json"].write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    targets["summary"].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8")
    print(format_summary(summary))
    return targets


def discover_pcaps(path: Path, recursive: bool) -> list[Path]:
    """Resolve one file or enumerate captures in a directory."""
    if path.is_file():
        return [path]
    if not path.exists():
        raise FileNotFoundError(f"Input does not exist: {path}")
    pattern = "**/*" if recursive else "*"
    return sorted(item for item in path.glob(pattern)
                  if item.is_file() and item.suffix.lower() in {".pcap", ".pcapng"})


def main() -> None:
    """Run the normalizer CLI."""
    config = load_config()
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("input", type=Path)
    cli.add_argument("--recursive", action="store_true")
    cli.add_argument("--overwrite", action="store_true")
    cli.add_argument("--port", type=int, default=config["modbus"]["port"])
    cli.add_argument("--output-directory", type=Path,
                     default=config["parser"]["output_directory"])
    args = cli.parse_args()
    paths = discover_pcaps(args.input, args.recursive)
    if not paths:
        cli.error(f"No PCAP files found under {args.input}")
    failures = 0
    for path in paths:
        try:
            outputs = normalize_pcap(path, args.output_directory, args.port,
                                     config["parser"]["schema_version"], args.overwrite)
            print("Generated:", ", ".join(str(item) for item in outputs.values()))
        except (PcapReadError, FileExistsError, OSError, ValueError) as exc:
            failures += 1
            print(f"ERROR {path}: {exc}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
