
import sys
import types

if "bpy" not in sys.modules:

    bpy = types.ModuleType("bpy")
    bpy_types = types.ModuleType("bpy.types")
    bpy_props = types.ModuleType("bpy.props")
    bpy_utils = types.ModuleType("bpy.utils")

    class PropertyGroup:
        pass

    class Operator:
        pass

    class Panel:
        pass

    class NodeTree:
        pass

    class ID:
        pass

    class Object(ID):
        pass

    class Collection(ID):
        pass

    class Scene(ID):
        pass

    class UILayout:
        pass

    class Material:
        pass

    class ColorRamp:
        pass

    class Context:
        pass

    for cls in (PropertyGroup, Operator, Panel, NodeTree, ID, Object,
                Collection, Scene, UILayout, Context, Material, ColorRamp):
        setattr(bpy_types, cls.__name__, cls)

    def _nop_property(*args, **kwargs):
        return None

    for name in ("PointerProperty", "StringProperty", "BoolProperty",
                 "IntProperty", "FloatProperty", "EnumProperty",
                 "CollectionProperty"):
        setattr(bpy_props, name, _nop_property)

    bpy_utils.register_class = lambda cls: None
    bpy_utils.unregister_class = lambda cls: None

    bpy.types = bpy_types
    bpy.props = bpy_props
    bpy.utils = bpy_utils

    sys.modules["bpy"] = bpy
    sys.modules["bpy.types"] = bpy_types
    sys.modules["bpy.props"] = bpy_props
    sys.modules["bpy.utils"] = bpy_utils

def foo():
    pass