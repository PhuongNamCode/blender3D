# Agent workflow

## Objective

Build reproducible, editable Blender scenes from source code and preserve the evidence of each successful build. A build is not complete until the generated `.blend`, render, log, and verification manifest are available.

## Agent roles

### Builder

- Owns `src/blender3d/scenes/`.
- Converts the requested design into named collections, objects, materials, cameras, lights, and render settings.
- Uses stable `bpy` APIs and rerunnable scripts.
- Does not overwrite a user's unrelated Blender file.

### Verifier

- Owns `src/blender3d/tools/` and the verification stage.
- Loads the generated `.blend` headlessly.
- Checks required collections and objects, render availability, file sizes, and basic scene invariants.
- Writes `verification.json`; a failed check returns a non-zero exit code.

### Reviewer/reviser

- Inspects the render, build log, and verification manifest.
- Separates confirmed failures from visual or modeling judgments.
- Patches only the relevant source code, then requests another build and verification.
- Does not mark a failed build as releasable.

### Release/commit agent

- Runs the complete build and verification gates.
- Reviews `git diff` and `git status` before committing.
- Commits source plus successful result artifacts together.
- Uses a descriptive commit message such as `build: add meeting room reference reconstruction`.
- Pushes only after the local commit contains the expected files and the remote is the user-provided repository.

## Required build gates

1. Blender starts successfully with the selected builder script.
2. The builder saves an editable `.blend` file and a PNG render.
3. The verifier finds the expected collections and key objects.
4. The render and `.blend` are non-empty and the manifest records their paths and sizes.
5. The render is visually inspected for camera occlusion, missing geometry, broken materials, and obviously incorrect scale.

If any gate fails, revise the source and rerun the build. Do not commit a failed result as a successful build.

## Artifact and revision policy

- Use a dated or explicitly named output directory for each meaningful build.
- Keep `build.log`, `verification.json`, the render, and the `.blend` together.
- Commit generated results when they are part of the requested deliverable; do not ignore `.blend` or PNG outputs by default.
- Ignore only temporary files such as `.blend1`, Python caches, and transient logs outside artifact directories.
- Preserve previous successful artifacts when revising so changes remain auditable.
