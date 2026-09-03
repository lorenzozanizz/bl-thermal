from .main_panel import MainPanel, ThermographyPanel, InfoPanel, CollectionSpecPanel, BakePanel
from .properties import (
    data_properties,
    scene_properties,
    SceneIgnoreRules,
    UniformTempProperties,
    WeightPaintedTempProperties,
    InitStrategyProperties,
    ThermalProperties,
    ThermalRenderSettings,
)

properties = data_properties + scene_properties


# PropertyGroup classes referenced via PointerProperty (Uniform/WeightPainted) must be
# registered before the class that points to them (InitStrategyProperties).
classes = (
    SceneIgnoreRules,
    UniformTempProperties,
    WeightPaintedTempProperties,
    InitStrategyProperties,
    ThermalProperties,
    ThermalRenderSettings,
    MainPanel,
    ThermographyPanel,
    BakePanel,
    CollectionSpecPanel,
    InfoPanel,
)
