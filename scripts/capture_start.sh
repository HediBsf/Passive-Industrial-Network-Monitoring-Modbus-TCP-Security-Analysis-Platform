#!/usr/bin/env sh
set -eu
TSHARK_PATH="${TSHARK_PATH:-tshark}"
INTERFACE="${CAPTURE_INTERFACE:-${1:-}}"
PORT="${MODBUS_PORT:-1502}"
OUTPUT="${2:-captures/normal/normal_$(date +%Y%m%d_%H%M%S).pcap}"
command -v "$TSHARK_PATH" >/dev/null 2>&1 || { echo "tshark not found; install Wireshark/tshark and grant capture permissions." >&2; exit 1; }
[ -n "$INTERFACE" ] || { "$TSHARK_PATH" -D; echo "Set CAPTURE_INTERFACE or pass interface as argument 1." >&2; exit 1; }
[ ! -e "$OUTPUT" ] || { echo "Refusing to overwrite $OUTPUT" >&2; exit 1; }
mkdir -p "$(dirname "$OUTPUT")"
"$TSHARK_PATH" -i "$INTERFACE" -f "tcp port $PORT" -w "$OUTPUT" >/dev/null 2>&1 &
PID=$!
printf '%s\n%s\n' "$PID" "$OUTPUT" > "$(dirname "$OUTPUT")/.capture.pid"
echo "Capture started PID=$PID path=$OUTPUT"
