from .main_panel import MainPanel, InfoPanel
from .properties import (
    data_properties,
    SceneIgnoreRules,
    UniformTempProperties,
    WeightPaintedTempProperties,
    InitStrategyProperties,
    ThermalProperties,
)

properties = data_properties

classes = (
    SceneIgnoreRules,
    UniformTempProperties,
    WeightPaintedTempProperties,
    InitStrategyProperties,
    ThermalProperties,
    MainPanel,
    InfoPanel,
)