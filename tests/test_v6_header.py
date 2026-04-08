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

if "--" in sys.argv:
    out_path = sys.argv[sys.argv.index("--") + 1]
else:
    raise SystemExit(
        "Usage: blender --background --factory-startup --python "
        "tests/test_v6_header.py -- <output.kn5>"
    )


def make_material_with_texture():
    """Principled BSDF + Image Texture wired to Base Color. moppius needs the
    full node graph to avoid a segfault during material write."""
    img = bpy.data.images.new(name="v6_tex", width=4, height=4, alpha=True)
    img.pixels = [1.0, 0.0, 0.0, 1.0] * 16
    img.pack()

    mat = bpy.data.materials.new(name="V6Mat")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.show_texture = True
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def main():
    # --factory-startup gives the default scene (cube+camera+light), not an
    # empty one — need read_factory_settings(use_empty=True) for a clean slate.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.name = "V6HeaderScene"

    mat = make_material_with_texture()

    mesh = bpy.data.meshes.new("Cube_mesh")
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
    mesh.materials.append(mat)
    obj = bpy.data.objects.new("Cube", mesh)
    bpy.context.collection.objects.link(obj)

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
