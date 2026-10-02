#!/usr/bin/env sh
set -eu
PID_FILE="${1:-$(find captures -name .capture.pid -print -quit)}"
[ -n "$PID_FILE" ] && [ -f "$PID_FILE" ] || { echo "No capture PID file found." >&2; exit 1; }
PID="$(sed -n '1p' "$PID_FILE")"
OUTPUT="$(sed -n '2p' "$PID_FILE")"
kill -INT "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
[ -s "$OUTPUT" ] || { echo "Capture missing or empty: $OUTPUT" >&2; exit 1; }
echo "$OUTPUT"
