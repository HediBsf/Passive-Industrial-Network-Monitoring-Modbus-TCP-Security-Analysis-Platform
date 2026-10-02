param(
    [ValidateSet("normal","rapid_polling","sensitive_write","dangerous_values")]
    [string]$Scenario = "normal",
    [int]$Duration = 60,
    [double]$Interval = 1.0,
    [string]$Interface = $env:CAPTURE_INTERFACE,
    [int]$Port = 1502
)
$ErrorActionPreference = "Stop"
$category = if ($Scenario -eq "normal") { "normal" } else { "abnormal" }
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$path = "captures\$category\$($Scenario)_$stamp.pcap"
& "$PSScriptRoot\capture_start.ps1" -Interface $Interface -Port $Port -OutputPath $path
try {
    Start-Sleep -Milliseconds 800
    python -m src.simulator.client --scenario $Scenario --duration $Duration --interval $Interval --port $Port
} finally {
    & "$PSScriptRoot\capture_stop.ps1" -PidFile "captures\$category\.capture.pid"
}
