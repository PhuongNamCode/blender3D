param(
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$SceneScript = Join-Path $RepoRoot "src\blender3d\scenes\meeting_room_reference.py"
$VerifyScript = Join-Path $RepoRoot "src\blender3d\tools\verify_scene.py"

if (-not $OutputDir) {
    $OutputDir = Join-Path $RepoRoot "artifacts\meeting_room_reference\2026-11-10"
} elseif (-not [System.IO.Path]::IsPathRooted($OutputDir)) {
    $OutputDir = Join-Path $RepoRoot $OutputDir
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$Blender = (Get-Command blender -ErrorAction SilentlyContinue).Source
if (-not $Blender) {
    $candidates = @(
        "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
        "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
        "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
    )
    $Blender = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $Blender) { throw "Blender executable was not found. Install Blender or add it to PATH." }

$env:BLENDER3D_OUTPUT_DIR = $OutputDir
$Log = Join-Path $OutputDir "build.log"
& $Blender --background --python $SceneScript 2>&1 | Tee-Object -FilePath $Log
if ($LASTEXITCODE -ne 0) { throw "Blender build failed. See $Log" }

& $Blender --background --python $VerifyScript 2>&1 | Tee-Object -FilePath $Log -Append
if ($LASTEXITCODE -ne 0) { throw "Verification failed. See $Log and verification.json" }

Write-Host "Build and verification passed: $OutputDir"
