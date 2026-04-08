"""Test 3 (substituted target): real .blend file with dynamic collection partition.

Opens a real scene (poc_track.blend), partitions its mesh objects into two
new collections, marks one excluded in the active view layer, runs the
patched moppius export, and verifies only the visible group lands in the KN5.

Why this exists: lingyun.blend triggers a Blender 5.1 mesh-tangent crash that
is unrelated to the moppius patch. poc_track.blend is a smaller real-world
scene (linked library, real material lacking active texture) that exercises
the patch without hitting the unrelated Blender bug.

Usage:
    blender --background --factory-startup --python tests/test_real_exclusion.py -- <input.blend> <out_dir>
"""
import sys
import os
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _fixtures import find_layer_collection  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2:
    raise SystemExit("Usage: blender --background --factory-startup --python tests/test_real_exclusion.py -- <input.blend> <out_dir>")
in_blend, out_dir = argv[0], argv[1]


def export(out_path, label):
    print(f"[{label}] view_layer.objects = {[o.name for o in bpy.context.view_layer.objects]}")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    try:
        result = bpy.ops.exporter.kn5(filepath=out_path)
        print(f"[{label}] exporter result: {result}")
    except Exception as e:
        print(f"[{label}] EXCEPTION: {type(e).__name__}: {e}")
        raise
    print(f"[{label}] OK: {out_path} ({os.path.getsize(out_path)} bytes)")


def main():
    print(f"opening {in_blend}")
    bpy.ops.wm.open_mainfile(filepath=in_blend)
    print(f"loaded: {len(bpy.data.objects)} obj / {len(bpy.data.collections)} extra coll")

    # Collect mesh objects directly under scene root
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    print(f"mesh objects: {[o.name for o in mesh_objs]}")
    if len(mesh_objs) < 2:
        raise SystemExit(f"FAIL: need at least 2 meshes, got {len(mesh_objs)}")

    # Partition: first mesh -> CollA_Visible, rest -> CollB_Hidden
    visible_mesh = mesh_objs[0]
    hidden_meshes = mesh_objs[1:]

    coll_a = bpy.data.collections.new("CollA_Visible_TEST")
    coll_b = bpy.data.collections.new("CollB_Hidden_TEST")
    bpy.context.scene.collection.children.link(coll_a)
    bpy.context.scene.collection.children.link(coll_b)

    # Move objects: unlink from scene collection, link to new collections
    for o in [visible_mesh] + hidden_meshes:
        for c in list(o.users_collection):
            try:
                c.objects.unlink(o)
            except RuntimeError:
                pass
    coll_a.objects.link(visible_mesh)
    for o in hidden_meshes:
        coll_b.objects.link(o)

    bpy.context.view_layer.update()

    visible_name = visible_mesh.name
    hidden_names = [o.name for o in hidden_meshes]
    print(f"VISIBLE_NAME = {visible_name}")
    print(f"HIDDEN_NAMES = {hidden_names}")

    bpy.ops.preferences.addon_enable(module="blender_assetto_corsa_tools")

    # Pass A: both collections included (sanity baseline for this rearranged scene)
    layer_b = find_layer_collection(bpy.context.view_layer.layer_collection, "CollB_Hidden_TEST")
    assert layer_b is not None
    layer_b.exclude = False
    bpy.context.view_layer.update()
    out_a = os.path.join(out_dir, "real_pass_a.kn5")
    export(out_a, "PASS_A_both_included")

    # Pass B: CollB excluded
    layer_b.exclude = True
    bpy.context.view_layer.update()
    out_b = os.path.join(out_dir, "real_pass_b.kn5")
    export(out_b, "PASS_B_collb_excluded")

    # Print sentinels for shell-side grep verification
    print(f"VERIFY_VISIBLE_NAME={visible_name}")
    for n in hidden_names:
        print(f"VERIFY_HIDDEN_NAME={n}")


if __name__ == "__main__":
    main()
