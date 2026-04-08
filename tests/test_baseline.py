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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _fixtures import reset_scene, make_image, make_material, make_cube  # noqa: E402

# Parse output path from argv after `--`
if "--" in sys.argv:
    out_path = sys.argv[sys.argv.index("--") + 1]
else:
    raise SystemExit("Usage: blender --background --factory-startup --python tests/test_baseline.py -- <output.kn5>")


def main():
    reset_scene("BaselineScene")
    img = make_image("baseline_tex", (1.0, 0.0, 0.0, 1.0))
    mat = make_material("baseline_mat", img)
    make_cube("Cube_A", (-2.0, 0.0, 0.0), mat)
    make_cube("Cube_B", (2.0, 0.0, 0.0), mat)
    bpy.ops.preferences.addon_enable(module="blender_assetto_corsa_tools")

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
