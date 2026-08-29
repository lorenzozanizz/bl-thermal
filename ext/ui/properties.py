"""
Blender-facing PropertyGroups mirroring the temperature-initialization
strategies defined in thermal_core/specs.py.

These hold live, editable UI state (attached to Object and Collection - see
`data_properties` at the bottom). A later conversion-boundary function
builds the pure `thermal_core.specs` dataclasses from this state right
before baking; nothing here should be consumed directly by physics code.

Both Object and Collection share the *same* InitStrategyProperties class.
The set of strategies offered in the dropdown differs per scope (Collection
can't offer WEIGHT_PAINTED - see ObjectTempInitType.allowed_for_scope() in
thermal_core/contracts.py) - resolved dynamically at draw time by checking
the type of the owning ID datablock (`self.id_data`), so we don't need two
near-duplicate PropertyGroup classes.
"""

from bpy.types import PropertyGroup, NodeTree, Object, Collection
from bpy.props import (
    PointerProperty, StringProperty, FloatProperty, EnumProperty,
)

from ..thermal_core.contracts import ObjectTempInitType, SpecScope
from ..thermal_core.temperature import TempUnit
from ..registration import PropertyRegistration


class SceneIgnoreRules(PropertyGroup):
    """ """
    pass


class UniformTempProperties(PropertyGroup):
    """ UI state for ObjectTempInitType.UNIFORM:
    a single scalar applied to every point on the object.
    """
    value: FloatProperty(                                               # type: ignore
        name="Temperature",
        description="Uniform starting temperature applied to every point on the object",
        default=293.15,  # 20C in Kelvin, stored/exposed per `unit` below
        soft_min=0.0,
    )
    unit: EnumProperty(                                                 # type: ignore
        name="Unit",
        description="Display unit for the temperature value above",
        items=[(u.name, u.value, "") for u in TempUnit],
        default=TempUnit.CELSIUS.name,
    )


class WeightPaintedTempProperties(PropertyGroup):
    """ UI state for ObjectTempInitType.WEIGHT_PAINTED. Object-only - see
    ObjectTempInitType.allowed_for_scope() in thermal_core/contracts.py.
    Weights (0-1) from `vertex_group` are remapped onto [min_value, max_value].
    """
    vertex_group: StringProperty(                                                       # type: ignore
        name="Vertex Group",
        description="Vertex group whose weights (0-1) are remapped to a temperature range",
    )
    min_value: FloatProperty(                                                           # type: ignore
        name="Min Temperature",
        description="Temperature at vertex-group weight 0.0",
        default=293.15,
    )
    max_value: FloatProperty(                                                           # type: ignore
        name="Max Temperature",
        description="Temperature at vertex-group weight 1.0",
        default=310.15,
    )
    unit: EnumProperty(                                                                 # type: ignore
        name="Unit",
        description="Display unit for the min/max temperature values above",
        items=[(u.name, u.value, "") for u in TempUnit],
        default=TempUnit.CELSIUS.name,
    )
    falloff: EnumProperty(                                                              # type: ignore
        name="Falloff",
        description="How intermediate weights are remapped between min and max",
        items=[
            ("LINEAR", "Linear", "Linear interpolation between min and max"),
            ("EASE_IN_OUT", "Ease In/Out", "Smoothstep interpolation between min and max"),
        ],
        default="LINEAR",
    )


# Needs to be declared at module level statically and cannot be put inside InitStrategyProperties due
# to blender registration requiring it
def _init_type_items(self, _):
    """ Determines scope (Object vs Collection) """
    scope = SpecScope.COLLECTION if isinstance(self.id_data, Collection) else SpecScope.OBJECT
    return [(m.name, m.value, "") for m in ObjectTempInitType.allowed_for_scope(scope)]


class InitStrategyProperties(PropertyGroup):
    """ "Which strategy, and its parameters" container, attached to both
    Object and Collection (see `data_properties`). Only the sub-group
    matching `init_type` is meaningful at any given time; the UI dispatcher
    (Phase 4) draws just that one via the strategy registry (Phase 3).
    """
    init_type: EnumProperty(                                                    # type: ignore
        name="Initial Temperature",
        description="Strategy used to determine the starting temperature",
        items=_init_type_items,                                                 # type: ignore
    )
    uniform: PointerProperty(type=UniformTempProperties)                        # type: ignore
    weight_painted: PointerProperty(type=WeightPaintedTempProperties)           # type: ignore


class ThermalProperties(PropertyGroup):
    """ Reserved for future physical thermal specs (emissivity, material)
    """
    pass


data_properties = (
    PropertyRegistration(
        owner=Object, name="thermal_init", value=PointerProperty(type=InitStrategyProperties)
    ),
    PropertyRegistration(
        owner=Collection, name="thermal_init", value=PointerProperty(type=InitStrategyProperties)
    ),
)