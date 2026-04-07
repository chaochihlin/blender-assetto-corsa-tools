"""Test 1 fixture+driver: baseline scene with no __ prefix and no exclusions.

Builds a deterministic scene in memory then runs the KN5 exporter. The
in-memory scene state is identical run-to-run, so the exported KN5 should
be byte-identical between two runs of the same addon code.

Usage:
    blender --background --factory-startup --python tests/test_baseline.py -- /tmp/out.kn5
"""
import sys
import os
import bpy

# Parse output path from argv after `--`
if "--" in sys.argv:
    out_path = sys.argv[sys.argv.index("--") + 1]
else:
    raise SystemExit("Usage: blender --background --factory-startup --python tests/test_baseline.py -- <output.kn5>")


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "BaselineScene"
    return scene


def make_image(name, color):
    img = bpy.data.images.new(name=name, width=4, height=4, alpha=True)
    pixels = list(color) * 16
    img.pixels = pixels
    img.pack()
    return img


def make_material(name, image):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.location = (-300, 0)
    tex.image = image
    tex.show_texture = True
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_cube(name, location, material):
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
    # Add a UV layer with deterministic coords
    mesh.uv_layers.new(name="UVMap")
    for loop in mesh.uv_layers.active.data:
        loop.uv = (0.0, 0.0)
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    bpy.context.collection.objects.link(obj)
    return obj


def enable_addon():
    addon_id = "blender_assetto_corsa_tools"
    try:
        bpy.ops.preferences.addon_enable(module=addon_id)
    except Exception as e:
        print(f"[test_baseline] addon_enable failed: {e}")
        raise


def main():
    reset_scene()
    img = make_image("baseline_tex", (1.0, 0.0, 0.0, 1.0))
    mat = make_material("baseline_mat", img)
    make_cube("Cube_A", (-2.0, 0.0, 0.0), mat)
    make_cube("Cube_B", (2.0, 0.0, 0.0), mat)
    enable_addon()

    # Force evaluation context
    bpy.context.view_layer.update()

    print(f"[test_baseline] view_layer.objects = {[o.name for o in bpy.context.view_layer.objects]}")
    print(f"[test_baseline] writing KN5 to {out_path}")
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    result = bpy.ops.exporter.kn5(filepath=out_path)
    print(f"[test_baseline] exporter result: {result}")
    if not os.path.exists(out_path):
        raise SystemExit(f"[test_baseline] FAIL: KN5 not created at {out_path}")
    size = os.path.getsize(out_path)
    print(f"[test_baseline] OK: {out_path} ({size} bytes)")


if __name__ == "__main__":
    main()
