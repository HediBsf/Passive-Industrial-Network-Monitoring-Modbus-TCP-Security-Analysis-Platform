#!/usr/bin/env sh
set -eu
SCENARIO="${1:-normal}"
DURATION="${2:-60}"
INTERVAL="${3:-1.0}"
PORT="${MODBUS_PORT:-1502}"
case "$SCENARIO" in normal) CATEGORY=normal;; rapid_polling|sensitive_write|dangerous_values) CATEGORY=abnormal;; *) echo "Invalid scenario" >&2; exit 2;; esac
OUTPUT="captures/$CATEGORY/${SCENARIO}_$(date +%Y%m%d_%H%M%S).pcap"
"$(dirname "$0")/capture_start.sh" "${CAPTURE_INTERFACE:-}" "$OUTPUT"
trap '"$(dirname "$0")/capture_stop.sh" "captures/'"$CATEGORY"'/.capture.pid"' EXIT INT TERM
sleep 1
python -m src.simulator.client --scenario "$SCENARIO" --duration "$DURATION" --interval "$INTERVAL" --port "$PORT"
