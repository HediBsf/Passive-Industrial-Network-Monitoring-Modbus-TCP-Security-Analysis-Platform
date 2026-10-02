"""Configuration loading with YAML, .env, and environment overrides."""
from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DEFAULTS: dict[str, Any] = {
    "modbus": {"host": "127.0.0.1", "port": 1502, "unit_id": 1,
                "update_interval_seconds": 1.0, "client_poll_interval_seconds": 1.0,
                "connection_retries": 10, "retry_delay_seconds": 2.0},
    "capture": {"interface": "", "tshark_path": "tshark",
                "output_directory": "captures", "default_duration_seconds": 60},
    "parser": {"output_directory": "results/parsed", "schema_version": "1.0",
               "recursive": False},
    "logging": {"level": "INFO", "directory": "logs"},
}
OVERRIDES = {
    "MODBUS_HOST": ("modbus", "host", str), "MODBUS_PORT": ("modbus", "port", int),
    "MODBUS_UNIT_ID": ("modbus", "unit_id", int),
    "MODBUS_UPDATE_INTERVAL": ("modbus", "update_interval_seconds", float),
    "MODBUS_CLIENT_INTERVAL": ("modbus", "client_poll_interval_seconds", float),
    "CAPTURE_INTERFACE": ("capture", "interface", str),
    "TSHARK_PATH": ("capture", "tshark_path", str),
    "LOG_LEVEL": ("logging", "level", str),
}


def _merge(base: dict[str, Any], extra: dict[str, Any]) -> None:
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load defaults, YAML, .env, and environment variables in that order."""
    load_dotenv(ROOT / ".env")
    config = deepcopy(DEFAULTS)
    config_path = Path(path) if path else ROOT / "config" / "settings.yaml"
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"Configuration root must be a mapping: {config_path}")
        _merge(config, loaded)
    for env_name, (section, key, caster) in OVERRIDES.items():
        if env_name in os.environ:
            try:
                config[section][key] = caster(os.environ[env_name])
            except ValueError as exc:
                raise ValueError(f"Invalid {env_name}: {os.environ[env_name]!r}") from exc
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    """Validate safety-critical and numeric configuration."""
    port = config["modbus"]["port"]
    if not 1 <= int(port) <= 65535:
        raise ValueError("Modbus port must be between 1 and 65535")
    if not 1 <= int(config["modbus"]["unit_id"]) <= 247:
        raise ValueError("Modbus unit_id must be between 1 and 247")
    for key in ("update_interval_seconds", "client_poll_interval_seconds",
                "retry_delay_seconds"):
        if float(config["modbus"][key]) <= 0:
            raise ValueError(f"modbus.{key} must be positive")
