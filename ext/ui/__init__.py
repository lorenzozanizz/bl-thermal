from .main_panel import (
    MainPanel, ThermographyPanel, InfoPanel, CollectionSpecPanel, BakePanel, EnvironmentPanel,
)
from .properties import (
    data_properties,
    scene_properties,
    SceneIgnoreRules,
    UniformTempProperties,
    AmbientTempProperties,
    WeightPaintedTempProperties,
    InitStrategyProperties,
    ThermalProperties,
    ThermalRenderSettings,
    EnvironmentAmbientTemperatureProperties,
    EnvironmentFactorItem,
    EnvironmentSettings,
)

properties = data_properties + scene_properties


# PropertyGroup classes referenced via PointerProperty (Uniform/WeightPainted) must be
# registered before the class that points to them (InitStrategyProperties). Likewise,
# EnvironmentAmbientTemperatureProperties must precede EnvironmentFactorItem, which must
# precede EnvironmentSettings.
classes = (
    SceneIgnoreRules,
    UniformTempProperties,
    AmbientTempProperties,
    WeightPaintedTempProperties,
    InitStrategyProperties,
    ThermalProperties,
    ThermalRenderSettings,
    EnvironmentAmbientTemperatureProperties,
    EnvironmentFactorItem,
    EnvironmentSettings,
    MainPanel,
    ThermographyPanel,
    BakePanel,
    CollectionSpecPanel,
    EnvironmentPanel,
    InfoPanel,
)