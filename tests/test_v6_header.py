"""Regression test: KN5FileWriter writes a valid V6 header.

V5 KN5 has a 10-byte header: magic(6) + version(uint32).
V6 KN5 has a 14-byte header: magic(6) + version(uint32) + reserved(uint32 = 0).

V6 is required for AC physics: V5 KN5 silently fails to spawn cars (they
fall through the floor). Verified empirically against ksEditor V6 output
in research/2026-04-05-ksEditor-vs-moppius-KN5結構比對.md.

Usage:
    blender --background --factory-startup --python tests/test_v6_header.py -- /tmp/v6.kn5
"""
import os
import struct
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _fixtures import reset_scene, make_image, make_material, make_cube  # noqa: E402

if "--" in sys.argv:
    out_path = sys.argv[sys.argv.index("--") + 1]
else:
    raise SystemExit(
        "Usage: blender --background --factory-startup --python "
        "tests/test_v6_header.py -- <output.kn5>"
    )


def main():
    reset_scene("V6HeaderScene")
    img = make_image("v6_tex", (1.0, 0.0, 0.0, 1.0))
    mat = make_material("V6Mat", img)
    make_cube("Cube", (0.0, 0.0, 0.0), mat)
    bpy.ops.preferences.addon_enable(module="blender_assetto_corsa_tools")
    bpy.context.view_layer.update()

    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    bpy.ops.exporter.kn5(filepath=out_path)

    with open(out_path, "rb") as f:
        header = f.read(14)
    assert len(header) == 14, f"file too small: {len(header)} bytes"

    magic = header[:6]
    version, reserved = struct.unpack("<II", header[6:14])

    assert magic == b"sc6969", f"bad magic: {magic!r}"
    assert version == 6, f"version is {version}, expected 6"
    assert reserved == 0, f"reserved field is {reserved}, expected 0"

    print(f"[test_v6_header] magic={magic!r} version={version} reserved={reserved}")
    print(f"[test_v6_header] OK: {out_path} ({os.path.getsize(out_path)} bytes)")


if __name__ == "__main__":
    main()
