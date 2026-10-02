# Traffic scenarios

| Scenario | Behavior | Classification and filename |
|---|---|---|
| normal | Starts motor, clears fault, periodically reads all mapped registers | `captures/normal/normal_<timestamp>.pcap` |
| rapid_polling | Repeatedly reads temperature at up to 20 requests/second | `captures/abnormal/rapid_polling_<timestamp>.pcap` |
| sensitive_write | Alternates motor command and occasionally sets fault; logs every write | `captures/abnormal/sensitive_write_<timestamp>.pcap` |
| dangerous_values | Writes high temperature, pressure, and vibration values | `captures/abnormal/dangerous_values_<timestamp>.pcap` |

Sensitive and dangerous scenarios restore safe commands/values in `finally` when communication remains available. All scenario entry points enforce localhost targets; they cannot be aimed at a remote industrial asset. These scenarios generate evidence for future detection work but do not issue alerts.
