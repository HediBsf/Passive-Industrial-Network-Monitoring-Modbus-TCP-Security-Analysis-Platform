# Usage

From the repository root:

```text
python -m src.simulator.server --host 127.0.0.1 --port 1502 --interval 1 --seed 42
python -m src.simulator.client --scenario normal --duration 60 --interval 1
python -m src.simulator.run_scenario --scenario rapid_polling --duration 30 --interval 0.02
python -m src.simulator.run_scenario --scenario sensitive_write --duration 30 --output-log logs/write.log
python -m src.simulator.run_scenario --scenario dangerous_values --duration 30
```

Capture:

```powershell
tshark -D
$env:CAPTURE_INTERFACE = "YOUR_LOOPBACK_INTERFACE"
.\scripts\capture_start.ps1 -Interface $env:CAPTURE_INTERFACE -Port 1502
.\scripts\capture_stop.ps1
.\scripts\capture_scenario.ps1 -Scenario normal -Duration 30
```

```bash
tshark -D
export CAPTURE_INTERFACE=lo
./scripts/capture_start.sh "$CAPTURE_INTERFACE"
./scripts/capture_stop.sh
./scripts/capture_scenario.sh normal 30 1
```

Parse one file or directories:

```text
python -m src.parser.normalizer captures/normal/example.pcap
python -m src.parser.normalizer captures/abnormal --recursive
python -m src.parser.normalizer captures --recursive --overwrite
```

Run validation with `python -m pytest -v`. Generated captures, results, and logs are ignored by Git.
