from .main_panel import MainPanel, InfoPanel, CollectionSpecPanel
from .properties import (
    data_properties,
    SceneIgnoreRules,
    UniformTempProperties,
    WeightPaintedTempProperties,
    InitStrategyProperties,
    ThermalProperties,
)

properties = data_properties


# PropertyGroup classes referenced via PointerProperty (Uniform/WeightPainted) must be registered before the
# class that points to them (InitStrategyProperties).
classes = (
    SceneIgnoreRules,
    UniformTempProperties,
    WeightPaintedTempProperties,
    InitStrategyProperties,
    ThermalProperties,
    MainPanel,
    CollectionSpecPanel,
    InfoPanel,
)