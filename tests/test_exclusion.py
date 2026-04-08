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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _fixtures import (  # noqa: E402
    reset_scene,
    make_image,
    make_material,
    make_cube,
    find_layer_collection,
)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not argv:
    raise SystemExit("Usage: blender --background --factory-startup --python tests/test_exclusion.py -- <output.kn5> [exclude|include]")
out_path = argv[0]
mode = argv[1] if len(argv) >= 2 else "exclude"
assert mode in ("exclude", "include"), f"mode must be exclude|include, got {mode}"


def main():
    reset_scene("ExclusionScene")
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
