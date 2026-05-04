param(
    [Parameter(Mandatory = $true)]
    [string]$XsaPath,
    [Parameter(Mandatory = $true)]
    [string]$Arch,
    [switch]$ForcePlatformRegen,
    [string]$StageRoot = 'C:\viterbi_stage\zu4ev',
    [string]$XsctBin = $(if ($env:XSCT_BIN) { $env:XSCT_BIN } else { 'E:\Xilinx\Vitis\2024.1\bin\xsct.bat' }),
    [string]$GccExe = $(if ($env:AARCH64_GCC) { $env:AARCH64_GCC } else { 'E:\Xilinx\Vitis\2024.1\gnu\aarch64\nt\aarch64-none\bin\aarch64-none-elf-gcc.exe' })
)

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).ProviderPath
$resolvedXsa = (Resolve-Path $XsaPath).ProviderPath

if (-not (Test-Path $XsctBin)) {
    throw "XSCT not found: $XsctBin"
}
if (-not (Test-Path $GccExe)) {
    throw "AArch64 GCC not found: $GccExe"
}

$stageDir = Join-Path $StageRoot $Arch
$workspace = Join-Path $stageDir 'xsct_ws'
$hwStage = Join-Path $stageDir 'hw'
$appStage = Join-Path $stageDir 'app'
$srcStage = Join-Path $appStage 'src'
$objStage = Join-Path $appStage 'obj'
$artifactDir = Join-Path $stageDir 'artifacts'
$platformName = "zu4ev_viterbi_$Arch"
$platformDir = Join-Path $workspace $platformName

function Test-PlatformArtifacts {
    param(
        [string]$PlatformDir,
        [string]$StagedXsa,
        [string]$ExpectedXsaHash
    )

    $bitBase = [System.IO.Path]::GetFileNameWithoutExtension($StagedXsa)
    $required = @(
        $PlatformDir,
        (Join-Path $PlatformDir 'psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0\include'),
        (Join-Path $PlatformDir 'psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0\lib\libxil.a'),
        (Join-Path $PlatformDir 'zynqmp_fsbl\fsbl_a53.elf'),
        (Join-Path $PlatformDir 'zynqmp_pmufw\pmufw.elf'),
        (Join-Path (Join-Path $PlatformDir 'hw') ($bitBase + '.bit'))
    )

    foreach ($path in $required) {
        if (-not (Test-Path $path)) {
            return $false
        }
    }

    $stampPath = Join-Path $PlatformDir '.xsa.sha256'
    if (-not (Test-Path $stampPath)) {
        return $false
    }
    $storedHash = (Get-Content -Path $stampPath -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
    if ($storedHash -ne $ExpectedXsaHash) {
        return $false
    }

    return $true
}

function Test-RequiredPaths {
    param([string[]]$Paths)

    $missing = @()
    foreach ($path in $Paths) {
        if (-not (Test-Path $path)) {
            $missing += $path
        }
    }
    return $missing
}

if ($ForcePlatformRegen) {
    Remove-Item -Recurse -Force $stageDir -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force -Path $workspace, $hwStage | Out-Null

$stagedXsa = Join-Path $hwStage (Split-Path $resolvedXsa -Leaf)
Copy-Item -Path $resolvedXsa -Destination $stagedXsa -Force
$currentXsaHash = (Get-FileHash -Algorithm SHA256 -Path $stagedXsa).Hash
$reusePlatform = Test-PlatformArtifacts -PlatformDir $platformDir -StagedXsa $stagedXsa -ExpectedXsaHash $currentXsaHash

if (-not $reusePlatform) {
    Remove-Item -Recurse -Force $workspace -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $workspace | Out-Null

    $env:XSCT_WORKSPACE = $workspace
    $env:PLATFORM_NAME = $platformName
    $env:XSA_PATH = $stagedXsa

    $xsctScript = Join-Path $repo 'scripts\xsct_create_zu4ev_platform.tcl'
    New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null
    $xsctLog = Join-Path $artifactDir 'xsct_platform.log'
    $savedErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $XsctBin $xsctScript 2>&1 | Tee-Object -FilePath $xsctLog | Out-Host
    $xsctExitCode = $LASTEXITCODE
    $ErrorActionPreference = $savedErrorActionPreference
    if ($xsctExitCode -ne 0) {
        $bitBase = [System.IO.Path]::GetFileNameWithoutExtension($stagedXsa)
        $requiredAfterXsct = @(
            $platformDir,
            (Join-Path $platformDir 'psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0\include'),
            (Join-Path $platformDir 'psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0\lib\libxil.a'),
            (Join-Path $platformDir 'zynqmp_fsbl\fsbl_a53.elf'),
            (Join-Path $platformDir 'zynqmp_pmufw\pmufw.elf'),
            (Join-Path (Join-Path $platformDir 'hw') ($bitBase + '.bit'))
        )
        $missingAfterXsct = Test-RequiredPaths -Paths $requiredAfterXsct
        if ($missingAfterXsct.Count -gt 0) {
            throw "XSCT platform generation failed and required artifacts are missing: $($missingAfterXsct -join ', '). See $xsctLog"
        }
        Write-Warning "XSCT returned $xsctExitCode after writing required platform artifacts; continuing. See $xsctLog"
    }

    Set-Content -Path (Join-Path $platformDir '.xsa.sha256') -Value $currentXsaHash -Encoding ASCII
} else {
    $xsctLog = Join-Path $artifactDir 'xsct_platform.log'
}

Remove-Item -Recurse -Force $appStage, $artifactDir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $srcStage, $objStage, $artifactDir | Out-Null

$bspRoot = Join-Path $platformDir 'psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0'
$includeDir = Join-Path $bspRoot 'include'
$libXil = Join-Path $bspRoot 'lib\libxil.a'
$fsblElf = Join-Path $platformDir 'zynqmp_fsbl\fsbl_a53.elf'
$pmufwElf = Join-Path $platformDir 'zynqmp_pmufw\pmufw.elf'
$bitPath = Join-Path (Join-Path $platformDir 'hw') (([System.IO.Path]::GetFileNameWithoutExtension($stagedXsa)) + '.bit')

foreach ($required in @($includeDir, $libXil, $fsblElf, $pmufwElf, $bitPath)) {
    if (-not (Test-Path $required)) {
        throw "Required platform artifact not found: $required"
    }
}

Copy-Item -Recurse -Path (Join-Path $repo 'vitis\zu4ev_baremetal\src\*') -Destination $srcStage -Force
$ldTemplate = Join-Path $repo 'vitis\zu4ev_baremetal\lscript_zu4ev.ld'
$ldScript = Join-Path $appStage 'lscript.ld'
Copy-Item -Path $ldTemplate -Destination $ldScript -Force

$includes = @(
    "-I$includeDir",
    "-I$srcStage",
    "-I$(Join-Path $srcStage 'generated')"
)
$commonCompileArgs = @(
    '-O2',
    '-g',
    '-Wall',
    '-Wextra',
    '-fno-tree-loop-distribute-patterns',
    '-mcpu=cortex-a53',
    '-march=armv8-a',
    '-c'
)

$sourceFiles = Get-ChildItem -Path $srcStage -Recurse -Filter '*.c' | Sort-Object FullName
$objectFiles = @()
foreach ($source in $sourceFiles) {
    $relative = $source.FullName.Substring($srcStage.Length).TrimStart('\')
    $objectPath = Join-Path $objStage ([System.IO.Path]::ChangeExtension($relative, '.o'))
    $objectDir = Split-Path $objectPath -Parent
    New-Item -ItemType Directory -Force -Path $objectDir | Out-Null
    & $GccExe @commonCompileArgs @includes '-o' $objectPath $source.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Compile failed for $($source.FullName)"
    }
    $objectFiles += $objectPath
}

$elfPath = Join-Path $artifactDir 'zu4ev_viterbi_test.elf'
$mapPath = Join-Path $artifactDir 'zu4ev_viterbi_test.map'
$linkArgs = @(
    '-mcpu=cortex-a53',
    '-march=armv8-a',
    '-Wl,--build-id=none',
    "-Wl,-T,$ldScript",
    "-Wl,-Map,$mapPath",
    '-Wl,--start-group'
) + $objectFiles + @(
    $libXil,
    '-lgcc',
    '-lc',
    '-Wl,--end-group',
    '-o',
    $elfPath
)

& $GccExe @linkArgs
if ($LASTEXITCODE -ne 0) {
    throw "Link failed for $elfPath"
}

$artifactInfo = [ordered]@{
    arch = $Arch
    generated_at = (Get-Date).ToString('s')
    xsa = $stagedXsa
    bit = $bitPath
    fsbl = $fsblElf
    pmufw = $pmufwElf
    elf = $elfPath
    map = $mapPath
    platform_dir = $platformDir
    bsp_root = $bspRoot
    xsct_log = $xsctLog
}

$artifactJson = Join-Path $artifactDir 'build_info.json'
$artifactInfo | ConvertTo-Json -Depth 4 | Set-Content -Path $artifactJson -Encoding utf8

Write-Host "Wrote $artifactJson"
Write-Host "ELF: $elfPath"
Write-Host "BIT: $bitPath"
