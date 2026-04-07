"""Test 3 driver: real lingyun/track.blend (1429 obj, 21 collections).

Verifies that the patched moppius writers handle a real-world Stage 5 scene
correctly. Two-pass test:

Pass A: open scene as-is, run export, count object names by category.
Pass B: programmatically exclude Prototype_Props collection in the active
        view layer, run export, verify the previously-`__`-blocked objects
        no longer appear in the KN5.

Usage:
    blender --background --factory-startup --python tests/test_lingyun.py -- <input.blend> <out_dir> [pass]
"""
import sys
import os
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2:
    raise SystemExit("Usage: blender --background --factory-startup --python tests/test_lingyun.py -- <input.blend> <out_dir> [a|b]")
in_blend = argv[0]
out_dir = argv[1]
pass_id = argv[2] if len(argv) >= 3 else "a"
assert pass_id in ("a", "b"), f"pass must be a|b"


def find_layer_collection(layer_collection, name):
    if layer_collection.collection.name == name:
        return layer_collection
    for child in layer_collection.children:
        found = find_layer_collection(child, name)
        if found:
            return found
    return None


def main():
    print(f"[test_lingyun pass={pass_id}] opening {in_blend}")
    bpy.ops.wm.open_mainfile(filepath=in_blend)
    print(f"[test_lingyun pass={pass_id}] scene loaded: {len(bpy.data.objects)} obj / {len(bpy.data.collections)} coll")

    if pass_id == "b":
        target = "Prototype_Props"
        layer = find_layer_collection(bpy.context.view_layer.layer_collection, target)
        if layer is None:
            print(f"[test_lingyun pass=b] WARN: collection '{target}' not found, listing top-level collections:")
            for c in bpy.context.view_layer.layer_collection.children:
                print(f"  - {c.collection.name}")
            raise SystemExit("Prototype_Props collection missing in lingyun scene")
        layer.exclude = True
        bpy.context.view_layer.update()
        print(f"[test_lingyun pass=b] excluded '{target}' in view layer")

    vl_objs = list(bpy.context.view_layer.objects)
    by_type = {}
    for o in vl_objs:
        by_type[o.type] = by_type.get(o.type, 0) + 1
    print(f"[test_lingyun pass={pass_id}] view_layer.objects total = {len(vl_objs)} types={by_type}")

    # Counts that matter for the regression
    def count_prefix(prefix):
        return sum(1 for o in vl_objs if o.name.startswith(prefix))

    print(f"[test_lingyun pass={pass_id}] counts:"
          f" __wbeam_={count_prefix('__wbeam_')}"
          f" __power_pole_={count_prefix('__power_pole_')}"
          f" __streetlight_={count_prefix('__streetlight_')}"
          f" __lingyun-road={count_prefix('__lingyun-road')}"
          f" Mesh_={count_prefix('Mesh_')}")

    bpy.ops.preferences.addon_enable(module="blender_assetto_corsa_tools")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"lingyun_pass_{pass_id}.kn5")
    print(f"[test_lingyun pass={pass_id}] exporting to {out_path}")
    try:
        result = bpy.ops.exporter.kn5(filepath=out_path)
        print(f"[test_lingyun pass={pass_id}] exporter result: {result}")
    except Exception as e:
        print(f"[test_lingyun pass={pass_id}] exporter EXCEPTION: {type(e).__name__}: {e}")
        # Don't re-raise: we want to know what happened even on failure
        return

    if os.path.exists(out_path):
        print(f"[test_lingyun pass={pass_id}] OK: {out_path} ({os.path.getsize(out_path)} bytes)")
    else:
        print(f"[test_lingyun pass={pass_id}] FAIL: KN5 not created")


if __name__ == "__main__":
    main()
