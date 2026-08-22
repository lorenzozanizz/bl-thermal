from enum import Enum
from dataclasses import dataclass

class ObjectTempInitType(Enum):
    """

    """
    GRADIENT = "Gradient"
    UNIFORM = "Uniform"
    AMBIENT = "Ambient"
    INHERIT = "Inherit"

class ObjectTempEvolution(Enum):
    """

    """
    FREE = "Free"
    FIXED = "Fixed"

class SimulationType(Enum):
    """

    """
    STATIONARY = "Stationary"
    DYNAMIC = "Dynamic"

class ThermographyType(Enum):
    """

    """
    TEMPERATURE = "Temperature"
    RADIANCE = "Radiance"
    RAYTRACE = "Raytrace"
