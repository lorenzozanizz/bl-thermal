""" Central mapping from ObjectTempInitType -> everything needed to work with
that strategy, like its class, the attribute it lives under on
InitStrategyProperties, how to build the pure thermal_core spec from it, and
how to draw its parameters.
"""

from typing import Type
from abc import ABC, abstractmethod

from bpy.types import PropertyGroup, UILayout, Object

from ..thermal_core.contracts import InitType, SpecScope
from ..thermal_core.specs import TempInitSpec, UniformTempSpec, WeightPaintedTempSpec
from ..thermal_core.temperature import TempUnit, Conversions
from .properties import UniformTempProperties, WeightPaintedTempProperties


class StrategyDescriptor(ABC):
    """ Everything needed to work with one temperature-init strategy.

    :param init_type: the ObjectTempInitType this descriptor implements.
    :param property_group: the bpy PropertyGroup class holding this
        strategy's parameters.
    :param attr_name: attribute name on InitStrategyProperties
    """
    init_type: InitType
    property_group: Type[PropertyGroup]
    attr_name: str

    @staticmethod
    @abstractmethod
    def draw(ui_layout: UILayout, props: PropertyGroup) -> None:
        pass

    @staticmethod
    @abstractmethod
    def build(props: PropertyGroup) -> TempInitSpec:
        pass


class InitStrategyRegistry:

    _REGISTRY = {}

    @staticmethod
    def get_strategy(init_type: InitType) -> StrategyDescriptor:
        """ Look up the descriptor for a strategy.  """
        if init_type is InitType.INHERIT:
            raise ValueError(
                "INHERIT has no StrategyDescriptor of its own it must be "
                "resolved to a concrete strategy first."
            )
        try:
            return InitStrategyRegistry._REGISTRY[init_type]
        except KeyError:
            raise NotImplementedError(
                f"{init_type!r} is defined in ObjectTempInitType but has no "
                f"StrategyDescriptor registered yet."
            ) from None

    @staticmethod
    def strategies_for_scope(scope: SpecScope) -> tuple[StrategyDescriptor, ...]:
        """ Return the descriptors that are both implemented
        and legal at the given scope, per ObjectTempInitType.allowed_for_scope().

        Skips INHERIT (not a real strategy) and silently skips allowed-but-
        unimplemented types like GRADIENT/AMBIENT rather than raising

        :param scope: the scope to look up the strategies for.
        """
        allowed = set(InitType.allowed_for_scope(scope))
        return tuple(
            descriptor for init_type, descriptor in InitStrategyRegistry._REGISTRY.items()
            if init_type in allowed
        )

    @classmethod
    def register(cls, init_type: InitType):
        def decorator(drawer_cls):
            cls._REGISTRY[init_type] = drawer_cls
            return drawer_cls
        return decorator


@InitStrategyRegistry.register(init_type=InitType.UNIFORM)
class InitWeightUniform(StrategyDescriptor):

    # Initialize the dataclass attribute
    init_type = InitType.UNIFORM
    property_group = UniformTempProperties
    attr_name = "uniform"

    @staticmethod
    def draw(layout: UILayout, props: UniformTempProperties) -> None:
        layout.prop(props, "value")
        layout.prop(props, "unit")

    @staticmethod
    def build(props: UniformTempProperties) -> UniformTempSpec:
        unit = TempUnit[props.unit]
        return UniformTempSpec(value_k=Conversions.to_kelvin(props.value, unit))


@InitStrategyRegistry.register(init_type=InitType.WEIGHT_PAINTED)
class InitWeightPainted(StrategyDescriptor):

    init_type = InitType.WEIGHT_PAINTED
    property_group = WeightPaintedTempProperties
    attr_name = "weight_painted"

    @staticmethod
    def draw(layout: UILayout, props: WeightPaintedTempProperties) -> None:
        # WEIGHT_PAINTED is Object-only, so props.id_data is normally an Object.
        # prop_search() renders a searchable dropdown against that object's
        # actual vertex groups instead of a string field, so a typo
        # or stale name can no longer be entered
        target = props.id_data
        if isinstance(target, Object) and target.type == 'MESH':
            layout.prop_search(props, "vertex_group", target, "vertex_groups")
        else:
            layout.prop(props, "vertex_group")
        layout.prop(props, "min_value")
        layout.prop(props, "max_value")
        layout.prop(props, "unit")
        layout.prop(props, "falloff")

    @staticmethod
    def build(props: WeightPaintedTempProperties) -> WeightPaintedTempSpec:
        unit = TempUnit[props.unit]
        return WeightPaintedTempSpec(
            vertex_group=props.vertex_group,
            min_k=Conversions.to_kelvin(props.min_value, unit),
            max_k=Conversions.to_kelvin(props.max_value, unit),
            falloff=props.falloff,
        )