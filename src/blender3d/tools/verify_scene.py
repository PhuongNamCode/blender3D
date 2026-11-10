import json
import os
from pathlib import Path

import bpy


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "meeting_room_reference" / "2026-11-10"
OUTPUT_DIR = Path(os.environ.get("BLENDER3D_OUTPUT_DIR", str(DEFAULT_OUTPUT)))
BLEND_FILE = OUTPUT_DIR / "meeting_room_reference_reconstruction.blend"
RENDER_FILE = OUTPUT_DIR / "meeting_room_reference_reconstruction.png"
MANIFEST_FILE = OUTPUT_DIR / "verification.json"

REQUIRED_COLLECTIONS = {"Architecture", "Furniture", "Equipment", "Lighting", "Decor"}
REQUIRED_OBJECTS = {
    "Floor",
    "Back wall",
    "Table A top",
    "TV screen",
    "Camera - reference room view",
    "Window daylight",
}


def verify():
    errors = []
    if not BLEND_FILE.exists() or BLEND_FILE.stat().st_size == 0:
        errors.append(f"Missing or empty Blender file: {BLEND_FILE}")
    if not RENDER_FILE.exists() or RENDER_FILE.stat().st_size == 0:
        errors.append(f"Missing or empty render: {RENDER_FILE}")

    if BLEND_FILE.exists() and BLEND_FILE.stat().st_size > 0:
        bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

    collections = {c.name for c in bpy.data.collections}
    objects = {o.name for o in bpy.data.objects}
    missing_collections = sorted(REQUIRED_COLLECTIONS - collections)
    missing_objects = sorted(REQUIRED_OBJECTS - objects)
    if missing_collections:
        errors.append(f"Missing collections: {missing_collections}")
    if missing_objects:
        errors.append(f"Missing objects: {missing_objects}")
    if len(objects) < 40:
        errors.append(f"Unexpectedly small scene: {len(objects)} objects")
    if bpy.context.scene.camera is None:
        errors.append("Scene has no active camera")

    manifest = {
        "status": "passed" if not errors else "failed",
        "blend_file": str(BLEND_FILE),
        "render_file": str(RENDER_FILE),
        "blend_bytes": BLEND_FILE.stat().st_size if BLEND_FILE.exists() else 0,
        "render_bytes": RENDER_FILE.stat().st_size if RENDER_FILE.exists() else 0,
        "object_count": len(objects),
        "collections": sorted(collections),
        "errors": errors,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return not errors


if __name__ == "__main__":
    if not verify():
        raise SystemExit(1)
