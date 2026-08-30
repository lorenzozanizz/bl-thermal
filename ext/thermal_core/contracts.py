from enum import Enum
from dataclasses import dataclass



class SpecScope(Enum):
    """ Where a temperature init spec is being attached/resolved. """
    OBJECT = "Object"
    COLLECTION = "Collection"


class InitType(Enum):
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

    @staticmethod
    def allowed_for_scope(scope: SpecScope) -> tuple:
        """ Return the subset of strategies that are legal at the given scope. """
        if scope is SpecScope.OBJECT:
            return _ALL_INITIALIZATION_STRATEGIES
        if scope is SpecScope.COLLECTION:
            return tuple(m for m in _ALL_INITIALIZATION_STRATEGIES if m not in _OBJECT_ONLY_STRATS)
        raise ValueError(f"Unknown scope: {scope}")


# These have to be put at the module level as any variable inside an Enum is still treated
# as an enum value and that causes issues with type hinting
# Strategies that require per-object data and cannot be a Collection-level default.
_ALL_INITIALIZATION_STRATEGIES = tuple(i_t for i_t in InitType)
_OBJECT_ONLY_STRATS = frozenset({InitType.WEIGHT_PAINTED})


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