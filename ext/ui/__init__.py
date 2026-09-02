from .main_panel import MainPanel, InfoPanel, CollectionSpecPanel
from .properties import (
    data_properties,
    scene_properties
)
from .properties import (
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
    CollectionSpecPanel,
    InfoPanel,
)
