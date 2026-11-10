import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "fcc-lab" / "2026-11-10"
OUTPUT = Path(os.environ.get("BLENDER3D_OUTPUT_DIR", str(DEFAULT_OUTPUT)))
OUTPUT.mkdir(parents=True, exist_ok=True)
BLEND_PATH = str(OUTPUT / "fcc_main_door_23010102_blockout.blend")
ENTRY_RENDER = str(OUTPUT / "fcc_main_door_23010102_entry.png")
CORRIDOR_RENDER = str(OUTPUT / "fcc_main_door_23010102_corridor.png")


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def get_collection(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    return col


COL = {name: get_collection(name) for name in ("Architecture", "Rooms", "Furniture", "Signs", "Lighting")}


def move(obj, target="Architecture"):
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    COL[target].objects.link(obj)


def material(name, color, roughness=0.55, metallic=0.0, emission=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission:
            bsdf.inputs["Emission Color"].default_value = (*emission[0], 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission[1]
    m.diffuse_color = (*color, 1.0)
    return m


MAT = {
    "wall": material("FCC warm white wall", (0.82, 0.80, 0.75), 0.82),
    "ceiling": material("FCC ceiling tile", (0.9, 0.88, 0.82), 0.9),
    "red_carpet": material("FCC lobby red carpet", (0.24, 0.045, 0.07), 0.98),
    "grey_carpet": material("FCC corridor grey carpet", (0.20, 0.22, 0.23), 0.98),
    "frame": material("Entrance aluminium frame", (0.26, 0.29, 0.28), 0.32, 0.75),
    "glass": material("Entrance glass", (0.20, 0.34, 0.38), 0.24, 0.15, emission=((0.04, 0.08, 0.10), 0.45)),
    "black": material("Display wall black", (0.008, 0.01, 0.012), 0.32),
    "screen": material("Screen blue black", (0.01, 0.035, 0.07), 0.15, 0.15),
    "wood": material("Kiosk light wood", (0.53, 0.36, 0.19), 0.62),
    "white": material("Furniture white", (0.86, 0.83, 0.77), 0.82),
    "green": material("Lounge green", (0.35, 0.52, 0.31), 0.86),
    "red": material("Lounge red", (0.55, 0.08, 0.08), 0.86),
    "metal": material("Furniture metal", (0.32, 0.34, 0.35), 0.32, 0.72),
    "fire": material("Fire extinguisher red", (0.65, 0.015, 0.01), 0.3),
    "light": material("Ceiling light", (0.92, 0.96, 1.0), 0.3, emission=((1.0, 0.9, 0.65), 3.0)),
}


def cube(name, location, dimensions, mat, target="Architecture", bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    move(obj, target)
    if bevel:
        mod = obj.modifiers.new("Soft edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return obj


def cylinder(name, location, radius, depth, mat, target="Furniture", rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    move(obj, target)
    return obj


def text(name, body, location, size=0.18, rotation=(math.pi / 2, 0, math.pi), mat=None):
    bpy.ops.object.text_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.004
    obj.data.materials.append(mat or MAT["black"])
    move(obj, "Signs")
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def room_shell(room_id, center_x, center_z, width, depth, height, floor_mat, open_sides=()):
    x, z = center_x, center_z
    cube(f"{room_id}_floor", (x, 0.0, z), (width, 0.08, depth), floor_mat, "Rooms")
    walls = {
        "west": ((x - width / 2, height / 2, z), (0.12, height, depth)),
        "east": ((x + width / 2, height / 2, z), (0.12, height, depth)),
        "north": ((x, height / 2, z + depth / 2), (width, height, 0.12)),
        "south": ((x, height / 2, z - depth / 2), (width, height, 0.12)),
    }
    for side, (loc, dims) in walls.items():
        if side not in open_sides:
            cube(f"{room_id}_{side}_wall", loc, dims, MAT["wall"], "Rooms", 0.02)
    room = bpy.data.objects.get(f"{room_id}_floor")
    if room:
        room["room_id"] = room_id
        room["source_status"] = "photo-guided provisional blockout"
        room["dimensions_status"] = "estimated; replace with measurements"
    return room


def add_door(name, x, z, width=1.0, height=2.2, wall="south", open_amount=0.0):
    if wall in ("south", "north"):
        obj = cube(name, (x, height / 2, z), (width, height, 0.06), MAT["glass"], "Architecture", 0.02)
        obj.rotation_euler[1] = open_amount
        cube(name + " frame", (x - width / 2, height / 2, z), (0.06, height + 0.08, 0.10), MAT["frame"], "Architecture")
        cube(name + " frame 2", (x + width / 2, height / 2, z), (0.06, height + 0.08, 0.10), MAT["frame"], "Architecture")
    else:
        obj = cube(name, (x, height / 2, z), (0.06, height, width), MAT["glass"], "Architecture", 0.02)
        cube(name + " frame", (x, height / 2, z - width / 2), (0.10, height + 0.08, 0.06), MAT["frame"], "Architecture")
        cube(name + " frame 2", (x, height / 2, z + width / 2), (0.10, height + 0.08, 0.06), MAT["frame"], "Architecture")
    return obj


def add_lounge_chair(name, x, z, mat):
    cube(name + " seat", (x, 0.42, z), (0.9, 0.18, 0.85), mat, "Furniture", 0.12)
    cube(name + " back", (x, 0.86, z + 0.28), (0.9, 0.8, 0.16), mat, "Furniture", 0.12)
    for dx in (-0.32, 0.32):
        cylinder(name + " leg", (x + dx, 0.18, z), 0.025, 0.36, MAT["metal"])


def add_table(name, x, z):
    cube(name + " top", (x, 0.48, z), (1.0, 0.08, 0.65), MAT["white"], "Furniture", 0.06)
    for dx in (-0.38, 0.38):
        cylinder(name + " leg", (x + dx, 0.24, z), 0.025, 0.42, MAT["metal"])


def add_scene():
    # Provisional local blockout: entry lobby 2.301, corridor, rooms 2.301.01/.02.
    room_shell("Room_2.301", 0.0, 0.0, 5.6, 4.6, 2.85, MAT["red_carpet"], open_sides=("south", "north"))
    room_shell("Room_2.301.01", 3.35, 4.6, 3.1, 3.7, 2.85, MAT["grey_carpet"], open_sides=("south",))
    room_shell("Room_2.301.02", -3.35, 4.6, 3.1, 3.7, 2.85, MAT["grey_carpet"], open_sides=("south",))
    cube("Corridor_floor", (0, 0.04, 5.45), (9.0, 0.08, 1.9), MAT["grey_carpet"], "Rooms")
    cube("Corridor_west_partition", (-4.5, 1.35, 5.45), (0.08, 2.7, 1.9), MAT["glass"], "Architecture")
    cube("Corridor_east_partition", (4.5, 1.35, 5.45), (0.08, 2.7, 1.9), MAT["glass"], "Architecture")

    # Main glazed entrance at the south side of 2.301.
    add_door("Main_Door_2.301_left", -0.78, -2.31, 1.45, 2.35, "south")
    add_door("Main_Door_2.301_right", 0.78, -2.31, 1.45, 2.35, "south")
    text("Main door room label", "2.301", (0, 2.48, -2.37), 0.25, (math.pi / 2, 0, 0), MAT["red"])
    text("Main door FCP", "FUTURE COMMUNICATIONS R&D PROGRAMME", (0, 2.35, -2.43), 0.12, (math.pi / 2, 0, 0), MAT["red"])

    # Door openings toward 2.301.01 and 2.301.02.
    add_door("Door_2.301.01", 3.35, 2.75, 1.0, 2.2, "south")
    add_door("Door_2.301.02", -3.35, 2.75, 1.0, 2.2, "south")
    text("Room label 2.301.01", "2.301.01", (3.35, 2.4, 2.70), 0.16, (math.pi / 2, 0, 0), MAT["black"])
    text("Room label 2.301.02", "2.301.02", (-3.35, 2.4, 2.70), 0.16, (math.pi / 2, 0, 0), MAT["black"])

    # Lobby display wall and two screen panels seen in the photo sequence.
    cube("Lobby display wall", (2.05, 1.35, 1.8), (0.16, 2.7, 1.7), MAT["black"], "Architecture", 0.02)
    for i, z in enumerate((1.2, 2.2), start=1):
        cube(f"Lobby screen {i}", (1.94, 2.05, z), (0.04, 0.65, 1.05), MAT["screen"], "Signs", 0.02)
    add_lounge_chair("Red lounge", 0.65, 1.1, MAT["red"])
    add_lounge_chair("Green lounge", 1.55, 1.0, MAT["green"])
    add_table("Lobby table", 1.1, 1.85)

    # Reception/kiosk visible just inside the entrance.
    cube("Information kiosk body", (-1.7, 0.7, -0.3), (0.95, 1.25, 0.75), MAT["wood"], "Furniture", 0.07)
    cube("Information kiosk screen", (-1.7, 1.38, -0.3), (0.03, 0.45, 0.62), MAT["screen"], "Furniture", 0.02)

    # Room 2.301.02: provisional office desks, chairs and rear blinds.
    for i, x in enumerate((-3.85, -2.9), start=1):
        cube(f"Room02 desk {i}", (x, 0.75, 4.9), (0.72, 0.08, 1.45), MAT["wood"], "Furniture", 0.03)
        add_lounge_chair(f"Room02 chair {i}", x, 4.05, MAT["black"])
    cube("Room02 window blind", (-3.35, 1.75, 6.38), (2.8, 1.9, 0.04), MAT["glass"], "Architecture")

    # Room 2.301.01: closed door, fire extinguisher and sidelight.
    cube("Room01 sidelight", (4.86, 1.4, 4.6), (0.04, 2.0, 0.6), MAT["glass"], "Architecture")
    cylinder("Room01 fire extinguisher", (4.72, 1.0, 3.7), 0.10, 0.55, MAT["fire"], "Furniture", rotation=(0, math.pi / 2, 0))

    # Corridor exit doors and ceiling fixtures.
    add_door("Corridor exit left", -0.7, 6.35, 0.75, 2.25, "north")
    add_door("Corridor exit right", 0.7, 6.35, 0.75, 2.25, "north")
    text("Exit sign", "EXIT", (0, 2.55, 6.15), 0.22, (math.pi / 2, 0, 0), MAT["light"])
    for x in (-2.8, 0, 2.8):
        cube(f"Lobby ceiling light {x}", (x, 2.82, 0.2), (0.22, 0.04, 1.2), MAT["light"], "Lighting", 0.01)
        cube(f"Corridor ceiling light {x}", (x, 2.82, 5.2), (0.22, 0.04, 1.2), MAT["light"], "Lighting", 0.01)


def add_cameras_lights():
    # Interior view back toward the glazed main entrance, matching the supplied lobby photos.
    bpy.ops.object.camera_add(location=(0, 1.65, 0.55))
    entry = bpy.context.object
    entry.name = "Camera_Entry"
    entry.data.lens = 24
    look_at(entry, (0, 1.25, -2.0))
    move(entry, "Lighting")

    bpy.ops.object.camera_add(location=(0, 1.65, 0.8))
    corridor = bpy.context.object
    corridor.name = "Camera_Corridor"
    corridor.data.lens = 25
    look_at(corridor, (0, 1.35, 5.8))
    move(corridor, "Lighting")

    for name, location, energy, size in (
        ("Lobby daylight", (-2.5, 2.7, 0.5), 950, 4.0),
        ("Corridor fill", (0, 2.7, 4.5), 650, 3.0),
        ("Entrance fill", (2.5, 2.2, -1.0), 500, 2.5),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.size = size
        look_at(light, (0, 0.8, 2.0))
        move(light, "Lighting")


def configure():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.035, 0.045, 0.055, 1.0)
        bg.inputs["Strength"].default_value = 0.25
    scene["source_scope"] = "FCC entrance 2.301 / rooms 2.301.01 and 2.301.02"
    scene["geometry_status"] = "provisional photo-guided blockout"
    scene["measurement_status"] = "unmeasured; replace estimated dimensions"


def main():
    clear_scene()
    add_scene()
    add_cameras_lights()
    configure()
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["Camera_Entry"]
    scene.render.filepath = ENTRY_RENDER
    bpy.ops.render.render(write_still=True)
    scene.camera = bpy.data.objects["Camera_Corridor"]
    scene.render.filepath = CORRIDOR_RENDER
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("Created:", BLEND_PATH)
    print("Rendered:", ENTRY_RENDER)
    print("Rendered:", CORRIDOR_RENDER)


if __name__ == "__main__":
    main()
