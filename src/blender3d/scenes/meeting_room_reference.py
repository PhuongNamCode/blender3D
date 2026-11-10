import bpy
import math
import os
from pathlib import Path
from mathutils import Vector


# Approximate reconstruction of the supplied meeting-room photographs.
# Dimensions are in metres and are intentionally editable rather than survey-accurate.

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "meeting_room_reference" / "2026-11-10"
OUT_DIR = Path(os.environ.get("BLENDER3D_OUTPUT_DIR", str(DEFAULT_OUTPUT)))
OUT_DIR.mkdir(parents=True, exist_ok=True)
BLEND_PATH = str(OUT_DIR / "meeting_room_reference_reconstruction.blend")
RENDER_PATH = str(OUT_DIR / "meeting_room_reference_reconstruction.png")


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        # Keep Blender's built-in datablocks; remove only unused generated data where possible.
        pass


def collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


COL = {name: collection(name) for name in ("Architecture", "Furniture", "Equipment", "Lighting", "Decor")}


def move_to_collection(obj, target):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    target.objects.link(obj)


def mat(name, color, roughness=0.55, metallic=0.0, emission=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission:
            bsdf.inputs["Emission Color"].default_value = (*emission[0], 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission[1]
    return m


M = {
    "wall": mat("Wall warm white", (0.86, 0.85, 0.79), 0.8),
    "ceiling": mat("Ceiling white", (0.93, 0.92, 0.86), 0.9),
    "floor": mat("Dark carpet", (0.075, 0.085, 0.09), 0.95),
    "blind": mat("Roller blind grey", (0.68, 0.69, 0.67), 0.82),
    "blind_white": mat("Roller blind white", (0.88, 0.88, 0.83), 0.82),
    "frame": mat("Window frame", (0.18, 0.19, 0.18), 0.45),
    "wood": mat("Light oak table", (0.68, 0.45, 0.23), 0.65),
    "wood_edge": mat("Table edge", (0.38, 0.22, 0.11), 0.6),
    "black": mat("Chair and rail black", (0.012, 0.015, 0.018), 0.38),
    "mesh": mat("Chair mesh", (0.025, 0.035, 0.04), 0.76),
    "cabinet": mat("Cabinet off white", (0.77, 0.75, 0.68), 0.7),
    "metal": mat("Brushed metal", (0.28, 0.3, 0.31), 0.35, 0.7),
    "screen": mat("TV inactive screen", (0.006, 0.012, 0.018), 0.15, 0.25),
    "screen_glow": mat("TV subtle reflection", (0.025, 0.045, 0.065), 0.12, 0.35),
    "door": mat("Door white", (0.82, 0.82, 0.78), 0.75),
    "red": mat("Small red accent", (0.5, 0.03, 0.02), 0.4),
    "light": mat("Ceiling light", (0.92, 0.97, 1.0), 0.25, emission=((1.0, 0.96, 0.82), 4.0)),
}


def cube(name, loc, scale, material, bevel=0.0, target="Architecture"):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        obj.data.materials.append(material)
    move_to_collection(obj, COL[target])
    if bevel:
        mod = obj.modifiers.new("Soft edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return obj


def cylinder(name, loc, radius, depth, material, rotation=(0, 0, 0), target="Equipment", vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    move_to_collection(obj, COL[target])
    return obj


def look_at(obj, point):
    direction = Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_wall_features():
    # Room envelope: 10 m wide x 8 m deep x 3.2 m high.
    cube("Floor", (0, 0, -0.06), (10, 8, 0.12), M["floor"], 0.02, "Architecture")
    cube("Back wall", (0, 3.94, 1.6), (10, 0.12, 3.2), M["wall"], 0.02, "Architecture")
    cube("Left wall", (-4.94, 0, 1.6), (0.12, 8, 3.2), M["wall"], 0.02, "Architecture")
    cube("Right wall", (4.94, 0, 1.6), (0.12, 8, 3.2), M["wall"], 0.02, "Architecture")
    cube("Ceiling", (0, 0, 3.25), (10, 8, 0.12), M["ceiling"], 0.02, "Architecture")

    # Three wide rear windows and roller blinds, matching the reference photos.
    for i, x in enumerate((-3.25, 0.0, 3.25), start=1):
        cube(f"Window recess {i}", (x, 3.875, 2.0), (3.05, 0.035, 2.45), M["frame"], 0.01, "Architecture")
        cube(f"Blind {i}", (x, 3.82, 2.05), (2.85, 0.035, 2.0), M["blind_white"] if i == 1 else M["blind"], 0.01, "Architecture")
        cylinder(f"Blind pull {i}", (x + 1.25, 3.76, 1.08), 0.012, 1.75, M["black"], target="Decor", vertices=12)
        cube(f"Blind top rail {i}", (x, 3.75, 3.1), (2.95, 0.07, 0.06), M["frame"], 0.01, "Architecture")

    # Door on the left/rear side.
    cube("Door frame", (-4.86, 2.35, 1.35), (0.08, 1.05, 2.7), M["frame"], 0.02, "Architecture")
    cube("Door", (-4.78, 2.35, 1.35), (0.06, 0.92, 2.55), M["door"], 0.02, "Architecture")
    cylinder("Door handle", (-4.69, 1.98, 1.35), 0.035, 0.12, M["metal"], rotation=(0, math.pi / 2, 0), target="Equipment", vertices=20)

    # Ceiling cable/lighting rails visible in all three photos.
    for y in (-2.85, 2.75):
        cylinder(f"Ceiling rail {y}", (0, y, 2.93), 0.055, 9.4, M["black"], rotation=(0, math.pi / 2, 0), target="Equipment")
        for x in (-3.6, 0.0, 3.6):
            cylinder(f"Rail hanger {x} {y}", (x, y, 3.08), 0.035, 0.3, M["black"], target="Equipment", vertices=16)

    # Four rectangular ceiling fixtures.
    for x in (-2.3, 2.3):
        for y in (-1.3, 2.3):
            cube(f"Ceiling panel light {x} {y}", (x, y, 3.16), (1.35, 0.32, 0.04), M["light"], 0.01, "Lighting")


def add_table(name, x, y, rotation=0.0):
    top = cube(name + " top", (x, y, 0.78), (2.45, 1.18, 0.12), M["wood"], 0.06, "Furniture")
    top.rotation_euler[2] = rotation
    # Legs are kept local-looking; visual accuracy is more important than joinery here.
    for sx in (-0.92, 0.92):
        for sy in (-0.39, 0.39):
            lx = x + sx * math.cos(rotation) - sy * math.sin(rotation)
            ly = y + sx * math.sin(rotation) + sy * math.cos(rotation)
            cube(name + " leg", (lx, ly, 0.39), (0.09, 0.09, 0.72), M["metal"], 0.02, "Furniture")
    return top


def add_chair(name, loc, rotation=0.0):
    x, y, z = loc
    seat = cube(name + " seat", (x, y, z + 0.48), (0.55, 0.55, 0.10), M["black"], 0.07, "Furniture")
    back = cube(name + " mesh back", (x, y + 0.22, z + 1.04), (0.58, 0.10, 0.92), M["mesh"], 0.08, "Furniture")
    stem = cylinder(name + " stem", (x, y, z + 0.25), 0.045, 0.42, M["metal"], target="Furniture", vertices=20)
    cylinder(name + " base", (x, y, z + 0.05), 0.35, 0.05, M["black"], target="Furniture", vertices=24)
    for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
        cylinder(name + " base arm", (x + 0.24 * math.cos(a), y + 0.24 * math.sin(a), z + 0.04), 0.025, 0.48, M["black"], rotation=(0, math.pi / 2, a), target="Furniture", vertices=12)
    for side in (-1, 1):
        arm_x = x + side * 0.36 * math.cos(rotation)
        arm_y = y + side * 0.36 * math.sin(rotation)
        # understated armrests, aligned approximately with the chair.
        cube(name + " armrest", (arm_x, arm_y, z + 0.82), (0.07, 0.42, 0.07), M["black"], 0.025, "Furniture")
    for o in (seat, back, stem):
        o.rotation_euler[2] = rotation


def add_furniture():
    # Four table modules form the central collaborative table seen in the photos.
    add_table("Table A", -1.28, -0.72)
    add_table("Table B", 1.28, -0.72)
    add_table("Table C", -1.28, 0.68)
    add_table("Table D", 1.28, 0.68)

    chair_positions = [
        (-3.0, -0.72, 0.0), (-3.0, 0.68, 0.0),
        (3.0, -0.72, math.pi), (3.0, 0.68, math.pi),
        (-1.28, -1.65, 0.0), (1.28, -1.65, 0.0),
        (-1.28, 1.6, math.pi), (1.28, 1.6, math.pi),
        (4.0, 2.0, math.pi / 2), (-4.0, 0.0, -math.pi / 2),
    ]
    for i, (x, y, r) in enumerate(chair_positions, start=1):
        add_chair(f"Office chair {i}", (x, y, 0.0), r)

    # Left-side tall storage cabinet from photograph 1.
    cube("Tall storage cabinet", (-4.25, 0.9, 1.25), (1.1, 1.75, 2.5), M["cabinet"], 0.025, "Furniture")
    cube("Cabinet door seam", (-3.68, 0.9, 1.25), (0.015, 1.65, 2.34), M["frame"], 0.005, "Furniture")
    for y in (0.55, 1.25):
        cube("Cabinet handle", (-3.64, y, 1.3), (0.035, 0.16, 0.32), M["metal"], 0.015, "Furniture")


def add_tv():
    # Large black display and low rolling stand, matching the first reference image.
    cube("TV screen", (4.25, 0.75, 1.9), (0.08, 3.25, 1.85), M["screen"], 0.025, "Equipment")
    cube("TV glass face", (4.19, 0.75, 1.9), (0.018, 3.05, 1.65), M["screen_glow"], 0.015, "Equipment")
    cube("TV pedestal", (4.13, 0.75, 0.86), (0.16, 0.22, 1.05), M["black"], 0.025, "Equipment")
    cube("TV rolling shelf", (4.10, 0.75, 0.34), (0.36, 2.3, 0.09), M["black"], 0.03, "Equipment")
    for y in (-0.15, 1.65):
        cylinder("TV stand wheel", (4.08, y, 0.14), 0.075, 0.08, M["black"], rotation=(0, math.pi / 2, 0), target="Equipment", vertices=20)


def add_camera_and_lights():
    # Interior viewpoint chosen to resemble the supplied room photographs.
    bpy.ops.object.camera_add(location=(-3.85, -3.45, 2.15))
    camera = bpy.context.object
    camera.name = "Camera - reference room view"
    camera.data.lens = 23
    camera.data.sensor_width = 36
    look_at(camera, (0.0, 1.75, 1.35))
    move_to_collection(camera, COL["Lighting"])
    bpy.context.scene.camera = camera

    # Soft daylight from the rear windows and a warm practical fill.
    bpy.ops.object.light_add(type="AREA", location=(0.0, 2.0, 2.95))
    key = bpy.context.object
    key.name = "Window daylight"
    key.data.energy = 850
    key.data.shape = "RECTANGLE"
    key.data.size = 6.5
    key.data.size_y = 2.4
    look_at(key, (0, 0, 0.7))
    move_to_collection(key, COL["Lighting"])

    bpy.ops.object.light_add(type="AREA", location=(-3.5, -2.5, 2.75))
    fill = bpy.context.object
    fill.name = "Room fill"
    fill.data.energy = 500
    fill.data.size = 4.0
    look_at(fill, (0, 0, 0.7))
    move_to_collection(fill, COL["Lighting"])

    bpy.ops.object.light_add(type="AREA", location=(3.6, 0.2, 2.6))
    edge = bpy.context.object
    edge.name = "TV side fill"
    edge.data.energy = 300
    edge.data.size = 2.5
    look_at(edge, (2.0, 0.7, 1.2))
    move_to_collection(edge, COL["Lighting"])


def configure_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    # Blender 5.2 exposes the real-time renderer as BLENDER_EEVEE.
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = RENDER_PATH
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.world.color = (0.035, 0.04, 0.05)
    world = scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.055, 0.065, 0.08, 1.0)
        bg.inputs["Strength"].default_value = 0.28


def main():
    clear_scene()
    add_wall_features()
    add_furniture()
    add_tv()
    add_camera_and_lights()
    configure_scene()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("Created:", BLEND_PATH)
    print("Rendered:", RENDER_PATH)


if __name__ == "__main__":
    main()
