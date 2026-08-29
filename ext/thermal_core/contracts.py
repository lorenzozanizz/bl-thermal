from enum import Enum
from dataclasses import dataclass



class SpecScope(Enum):
    """ Where a temperature init spec is being attached/resolved. """
    OBJECT = "Object"
    COLLECTION = "Collection"


class ObjectTempInitType(Enum):
    """ Strategy used to initialize an object's starting temperature field.

    Not every strategy is valid at every configuration, for example
    WEIGHT_PAINTED depends on per-vertex data (a vertex group) that only exists on a
    mesh Object, so it can never be used as a Collection-level default.
    """

    GRADIENT = "Gradient"
    UNIFORM = "Uniform"
    AMBIENT = "Ambient"
    WEIGHT_PAINTED = "Weight Painted"
    INHERIT = "Inherit"

    # Strategies that require per-object data and cannot be a
    # Collection-level default.
    _OBJECT_ONLY = frozenset({WEIGHT_PAINTED})


    @classmethod
    def allowed_for_scope(cls, scope: SpecScope) -> tuple["ObjectTempInitType", ...]:
        """ Return the subset of strategies that are legal at the given scope. """
        if scope is SpecScope.OBJECT:
            return tuple(cls)
        if scope is SpecScope.COLLECTION:
            return tuple(m for m in cls if m not in ObjectTempInitType._OBJECT_ONLY)
        raise ValueError(f"Unknown scope: {scope}")

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