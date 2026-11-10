# blender3D

An agent-oriented Blender 3D development project. The repository keeps scene source code, deterministic build commands, verification checks, and the result of each successful build together.

## Project layout

```text
src/blender3d/scenes/     Blender scene builders
src/blender3d/tools/      Headless verification and reporting tools
scripts/                  Windows build and verification entry points
artifacts/<scene>/<date>/ Render, .blend, log, and verification manifest
AGENTS.md                 Agent roles, gates, and commit protocol
```

## Build the reference scene

From PowerShell at the repository root:

```powershell
.\scripts\build_scene.ps1
```

The script detects Blender, runs the scene builder headlessly, writes the `.blend` and PNG render under `artifacts/`, and then runs verification. You can override the output directory:

```powershell
.\scripts\build_scene.ps1 -OutputDir artifacts\meeting_room_reference\my-run
```

To verify an existing build without rebuilding:

```powershell
.\scripts\verify_scene.ps1 -OutputDir artifacts\meeting_room_reference\2026-11-10
```

## Development loop

1. Modify a scene builder under `src/blender3d/scenes/`.
2. Run the build script.
3. Inspect the rendered PNG and `verification.json`.
4. Revise the scene code when the render or checks reveal a problem.
5. Rebuild and verify again.
6. Commit the source and successful artifacts together.

The current scene is an approximate editable reconstruction of the supplied meeting-room photographs; it is not a dimensionally surveyed model.
