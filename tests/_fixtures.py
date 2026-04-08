"""Shared scene-build helpers for moppius regression tests.

All four test scripts (test_baseline, test_exclusion, test_v6_header,
test_real_exclusion) historically duplicated near-identical fixture code.
This module is the single source of truth for those primitives.

Tests import this module by adding the tests/ directory to sys.path before
the import. Each test runs in its own `blender --background` process so
there's no cross-test state leakage.
"""
import bpy


def reset_scene(name):
    """Wipe the current Blender state to an empty scene with the given name.

    Note: --factory-startup loads Blender's *default* scene (cube + camera
    + light), not an empty one. read_factory_settings(use_empty=True) is
    required for a clean slate.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = name
    return scene


def make_image(name, color):
    """4x4 packed image filled with a single RGBA color."""
    img = bpy.data.images.new(name=name, width=4, height=4, alpha=True)
    img.pixels = list(color) * 16
    img.pack()
    return img


def make_material(name, image):
    """Principled BSDF + Image Texture wired to Base Color.

    moppius requires the full node graph (BSDF + Image Texture node) to
    write a complete material; a bare `use_nodes = True` material segfaults
    the texture writer on minimal scenes.
    """
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


def make_cube(name, location, material, collection=None):
    """Unit cube with a UV layer and the given material assigned.

    If collection is None, links to bpy.context.collection (the active one).
    """
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
    target = collection if collection is not None else bpy.context.collection
    target.objects.link(obj)
    return obj


def find_layer_collection(layer_collection, name):
    """Recursively find a LayerCollection by its underlying collection name."""
    if layer_collection.collection.name == name:
        return layer_collection
    for child in layer_collection.children:
        found = find_layer_collection(child, name)
        if found:
            return found
    return None
