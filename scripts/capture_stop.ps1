param([string]$PidFile = "")
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($PidFile)) {
    $match = Get-ChildItem -Path captures -Filter ".capture.pid" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $match) { throw "No capture PID file found under captures." }
    $PidFile = $match.FullName
}
$lines = Get-Content -LiteralPath $PidFile
$capturePid = [int]$lines[0]
$capturePath = $lines[1]
$process = Get-Process -Id $capturePid -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $capturePid
    $process.WaitForExit()
}
Remove-Item -LiteralPath $PidFile -Force
if (-not (Test-Path -LiteralPath $capturePath) -or (Get-Item -LiteralPath $capturePath).Length -eq 0) {
    throw "Capture is missing or empty: $capturePath"
}
Write-Output $capturePath
