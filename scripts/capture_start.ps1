param(
    [string]$Interface = $env:CAPTURE_INTERFACE,
    [int]$Port = $(if ($env:MODBUS_PORT) { [int]$env:MODBUS_PORT } else { 1502 }),
    [string]$OutputPath = "",
    [string]$TsharkPath = $(if ($env:TSHARK_PATH) { $env:TSHARK_PATH } else { "tshark" })
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command $TsharkPath -ErrorAction SilentlyContinue)) {
    throw "tshark was not found. Install Wireshark with Npcap and add tshark to PATH (or set TSHARK_PATH)."
}
if ([string]::IsNullOrWhiteSpace($Interface)) {
    & $TsharkPath -D
    throw "No capture interface selected. Set CAPTURE_INTERFACE or pass -Interface. Choose the Npcap loopback adapter for localhost traffic."
}
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputPath = "captures\normal\normal_$stamp.pcap"
}
$resolvedParent = [IO.Path]::GetFullPath((Split-Path $OutputPath -Parent))
New-Item -ItemType Directory -Force -Path $resolvedParent | Out-Null
if (Test-Path -LiteralPath $OutputPath) { throw "Capture already exists: $OutputPath" }
$process = Start-Process -FilePath $TsharkPath -ArgumentList @("-i",$Interface,"-f","tcp port $Port","-w",$OutputPath) -PassThru -WindowStyle Hidden
$pidFile = Join-Path $resolvedParent ".capture.pid"
@($process.Id, [IO.Path]::GetFullPath($OutputPath)) | Set-Content -LiteralPath $pidFile -Encoding utf8
Write-Output "Capture started PID=$($process.Id) path=$([IO.Path]::GetFullPath($OutputPath))"
