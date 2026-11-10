param([string]$OutputDir = "")
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Scene = Join-Path $RepoRoot "src\blender3d\scenes\fcc_main_door_23010102.py"
$Verify = Join-Path $RepoRoot "src\blender3d\tools\verify_fcc_main_door.py"
if (-not $OutputDir) { $OutputDir = Join-Path $RepoRoot "artifacts\fcc-lab\2026-11-10" }
elseif (-not [IO.Path]::IsPathRooted($OutputDir)) { $OutputDir = Join-Path $RepoRoot $OutputDir }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$Blender = (Get-Command blender -ErrorAction SilentlyContinue).Source
if (-not $Blender) { $Blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" }
if (-not (Test-Path $Blender)) { throw "Blender executable was not found." }
$env:BLENDER3D_OUTPUT_DIR = $OutputDir
$Log = Join-Path $OutputDir "fcc_main_door_build.log"
& $Blender --background --python $Scene 2>&1 | Tee-Object -FilePath $Log
if ($LASTEXITCODE -ne 0) { throw "FCC entrance Blender build failed. See $Log" }
& $Blender --background --python $Verify 2>&1 | Tee-Object -FilePath $Log -Append
if ($LASTEXITCODE -ne 0) { throw "FCC entrance verification failed." }
Write-Host "FCC entrance build and verification passed: $OutputDir"
