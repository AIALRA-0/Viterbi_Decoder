param(
    [Parameter(Mandatory = $true)]
    [string]$BuildInfoPath,
    [string]$HwServerUrl = 'tcp:127.0.0.1:3121',
    [string]$VivadoBin = $(if ($env:VIVADO_BIN) { $env:VIVADO_BIN } else { 'E:\Xilinx\Vivado\2024.1\bin' }),
    [string]$XsctBin = $(if ($env:XSCT_BIN) { $env:XSCT_BIN } else { 'E:\Xilinx\Vitis\2024.1\bin\xsct.bat' })
)

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).ProviderPath
$buildInfo = Get-Content -Raw $BuildInfoPath | ConvertFrom-Json
$hwServerBat = Join-Path $VivadoBin 'hw_server.bat'

if (-not (Test-Path $hwServerBat)) {
    throw "hw_server not found: $hwServerBat"
}
if (-not (Test-Path $XsctBin)) {
    throw "XSCT not found: $XsctBin"
}

foreach ($required in @($buildInfo.bit, $buildInfo.pmufw, $buildInfo.fsbl, $buildInfo.elf)) {
    if (-not (Test-Path $required)) {
        throw "Required programming artifact not found: $required"
    }
}

$listener = Get-NetTCPConnection -LocalPort 3121 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
$startedHwServer = $null
if (-not $listener) {
    $startedHwServer = Start-Process -FilePath $hwServerBat -ArgumentList '-s', 'tcp::3121' -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

$env:HW_SERVER_URL = $HwServerUrl
$env:BIT_PATH = [string]$buildInfo.bit
$env:PMUFW_PATH = [string]$buildInfo.pmufw
$env:FSBL_PATH = [string]$buildInfo.fsbl
$env:APP_ELF_PATH = [string]$buildInfo.elf

$xsctScript = Join-Path $repo 'scripts\xsct_program_zu4ev.tcl'
$programLog = Join-Path (Split-Path $BuildInfoPath -Parent) 'program.log'

try {
    & $XsctBin $xsctScript 2>&1 | Tee-Object -FilePath $programLog | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Programming failed. See $programLog"
    }
} finally {
    if ($startedHwServer -and -not $startedHwServer.HasExited) {
        Stop-Process -Id $startedHwServer.Id -Force
    }
}

Write-Host "Wrote $programLog"
