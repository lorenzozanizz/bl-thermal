"""
Pure data contracts describing how an object's/collection's initial
temperature field is specified.

"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from .temperature import Conversions
from .contracts import InitType


@dataclass(frozen=True)
class TempInitSpec(ABC):
    """ Base class for a single temperature-initialization strategy.

    Concrete subclasses correspond 1:1 with an `ObjectTempInitType` member
    (excluding INHERIT, which is a resolution-time concept, not a spec - by
    the time a TempInitSpec exists, inheritance has already been resolved to
    a concrete strategy).
    """

    @property
    @abstractmethod
    def init_type(self) -> InitType:
        """ The ObjectTempInitType this spec implements. """
        raise NotImplementedError

    def validate(self) -> None:
        """ Raise ValueError if the spec's parameters are physically invalid.
        Subclasses should extend this rather than overriding it outright.
        """
        pass

    @staticmethod
    def get_vertex_group() -> Optional[str]:
        """ Returns true if the initialization strategy requires some kind of
        vertex weighing, which will be extracted from the returned value """
        return None


@dataclass(frozen=True)
class UniformTempSpec(TempInitSpec):
    """ Every point on the object starts at the same temperature. """
    value_k: float

    @property
    def init_type(self) -> InitType:
        return InitType.UNIFORM

    def validate(self) -> None:
        if not Conversions.is_physically_valid_kelvin(self.value_k):
            raise ValueError(f"UniformTempSpec.value_k ({self.value_k}K) is below absolute zero")


@dataclass(frozen=True)
class WeightPaintedTempSpec(TempInitSpec):
    """ Temperature is derived by remapping a vertex group's per-vertex
    weight (0-1) onto a [min_k, max_k] range.
    """
    vertex_group: str
    min_k: float
    max_k: float
    falloff: str = "LINEAR"  # matches a future Blender CurveMapping/enum choice

    @property
    def init_type(self) -> InitType:
        return InitType.WEIGHT_PAINTED

    def validate(self) -> None:
        if not self.vertex_group:
            raise ValueError("WeightPaintedTempSpec.vertex_group must not be empty")
        if (not Conversions.is_physically_valid_kelvin(self.min_k) or
                not Conversions.is_physically_valid_kelvin(self.max_k)):
            raise ValueError(f"Extrema values below absolute zero for the spec")
        if self.min_k > self.max_k:
            raise ValueError(f"WeightPaintedTempSpec.min_k ({self.min_k}) must be <= max_k ({self.max_k})")

    def get_vertex_group(self) -> str:
        """ This strategy requires weights. """
        return self.vertex_group

@dataclass
class ThermalProfile:
    """ Holds a complete profile: how an object's temperature is initialized,
    plus (in a later phase) how it evolves over time. Kept minimal for now -
    evolution strategy will be added once thermal_core/evolution.py is built out.
    """
    init_spec: TempInitSpec


class ThermalSpecs:
    """
    Holds purely physical thermal specs (emissivity, material properties,
    etc). Out of scope for Phase 1 - untouched here.
    """