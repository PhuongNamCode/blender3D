import json
import os
from pathlib import Path

import bpy


REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(os.environ.get("BLENDER3D_OUTPUT_DIR", str(REPO_ROOT / "artifacts" / "fcc-lab" / "2026-11-10")))
BLEND = OUTPUT / "fcc_main_door_23010102_blockout.blend"
RENDERS = [OUTPUT / "fcc_main_door_23010102_entry.png", OUTPUT / "fcc_main_door_23010102_corridor.png"]
MANIFEST = OUTPUT / "fcc_main_door_23010102_verification.json"

REQUIRED = {
    "Room_2.301_floor",
    "Room_2.301.01_floor",
    "Room_2.301.02_floor",
    "Main_Door_2.301_left",
    "Main_Door_2.301_right",
    "Door_2.301.01",
    "Door_2.301.02",
    "Camera_Entry",
    "Camera_Corridor",
}


def main():
    errors = []
    if not BLEND.exists() or BLEND.stat().st_size == 0:
        errors.append(f"Missing blend: {BLEND}")
    for render in RENDERS:
        if not render.exists() or render.stat().st_size == 0:
            errors.append(f"Missing render: {render}")
    if BLEND.exists() and BLEND.stat().st_size:
        bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    objects = {obj.name for obj in bpy.data.objects}
    missing = sorted(REQUIRED - objects)
    if missing:
        errors.append(f"Missing required objects: {missing}")
    if bpy.context.scene.camera is None:
        errors.append("No active camera")
    manifest = {
        "status": "passed" if not errors else "failed",
        "blend": str(BLEND),
        "renders": [str(r) for r in RENDERS],
        "blend_bytes": BLEND.stat().st_size if BLEND.exists() else 0,
        "render_bytes": {str(r): r.stat().st_size if r.exists() else 0 for r in RENDERS},
        "object_count": len(objects),
        "required_objects": sorted(REQUIRED),
        "errors": errors,
        "geometry_status": "provisional photo-guided blockout",
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
