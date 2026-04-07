"""Test 2 fixture+driver: scene with two collections, one excluded in view layer.

Verifies that the patched moppius writers respect Outliner collection exclusion.

Usage:
    blender --background --factory-startup --python tests/test_exclusion.py -- /tmp/out.kn5 [exclude|include]

Argument:
    exclude (default): collection B is excluded; only Cube_Visible should appear in KN5
    include          : collection B is included; both Cube_Visible and Cube_Hidden appear
"""
import sys
import os
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not argv:
    raise SystemExit("Usage: blender --background --factory-startup --python tests/test_exclusion.py -- <output.kn5> [exclude|include]")
out_path = argv[0]
mode = argv[1] if len(argv) >= 2 else "exclude"
assert mode in ("exclude", "include"), f"mode must be exclude|include, got {mode}"


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.name = "ExclusionScene"


def make_image(name, color):
    img = bpy.data.images.new(name=name, width=4, height=4, alpha=True)
    img.pixels = list(color) * 16
    img.pack()
    return img


def make_material(name, image):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.show_texture = True
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_cube(name, location, material, collection):
    mesh = bpy.data.meshes.new(name + "_mesh")
    verts = [
        (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
        (-0.5, -0.5, 0.5),  (0.5, -0.5, 0.5),  (0.5, 0.5, 0.5),  (-0.5, 0.5, 0.5),
    ]
    faces = [
        (0, 1, 2, 3), (4, 5, 6, 7),
        (0, 1, 5, 4), (1, 2, 6, 5),
        (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.uv_layers.new(name="UVMap")
    for loop in mesh.uv_layers.active.data:
        loop.uv = (0.0, 0.0)
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    collection.objects.link(obj)
    return obj


def find_layer_collection(layer_collection, name):
    if layer_collection.collection.name == name:
        return layer_collection
    for child in layer_collection.children:
        found = find_layer_collection(child, name)
        if found:
            return found
    return None


def main():
    reset_scene()
    img = make_image("excl_tex", (0.0, 1.0, 0.0, 1.0))
    mat = make_material("excl_mat", img)

    scene = bpy.context.scene
    coll_a = bpy.data.collections.new("CollA_Visible")
    coll_b = bpy.data.collections.new("CollB_Hidden")
    scene.collection.children.link(coll_a)
    scene.collection.children.link(coll_b)

    make_cube("Cube_Visible", (-2, 0, 0), mat, coll_a)
    make_cube("Cube_Hidden", (2, 0, 0), mat, coll_b)

    # Set view layer exclusion on CollB based on mode
    bpy.context.view_layer.update()
    layer_b = find_layer_collection(bpy.context.view_layer.layer_collection, "CollB_Hidden")
    assert layer_b is not None, "CollB_Hidden layer collection not found"
    layer_b.exclude = (mode == "exclude")
    bpy.context.view_layer.update()

    bpy.ops.preferences.addon_enable(module="blender_assetto_corsa_tools")

    print(f"[test_exclusion mode={mode}] view_layer.objects = {[o.name for o in bpy.context.view_layer.objects]}")
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    result = bpy.ops.exporter.kn5(filepath=out_path)
    print(f"[test_exclusion mode={mode}] exporter result: {result}")
    print(f"[test_exclusion mode={mode}] OK: {out_path} ({os.path.getsize(out_path)} bytes)")


if __name__ == "__main__":
    main()
