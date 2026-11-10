param(
    [string]$OutputDir = "artifacts\meeting_room_reference\2026-11-10"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$VerifyScript = Join-Path $RepoRoot "src\blender3d\tools\verify_scene.py"
if (-not [System.IO.Path]::IsPathRooted($OutputDir)) { $OutputDir = Join-Path $RepoRoot $OutputDir }
if (-not (Test-Path $OutputDir)) { throw "Artifact directory does not exist: $OutputDir" }

$Blender = (Get-Command blender -ErrorAction SilentlyContinue).Source
if (-not $Blender) { $Blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" }
if (-not (Test-Path $Blender)) { throw "Blender executable was not found." }

$env:BLENDER3D_OUTPUT_DIR = $OutputDir
& $Blender --background --python $VerifyScript
if ($LASTEXITCODE -ne 0) { throw "Verification failed for $OutputDir" }
