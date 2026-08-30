"""
Pure numeric evaluation of a resolved TempInitSpec into a per-vertex Kelvin
array.

This is the bpy-free counterpart to ui/init_registry.py.
This registry maps a spec class to the numeric evaluate() behaviour that turns
it into actual per-vertex values.

Anything requiring bpy (vertex count, named vertex-group weights, ...) is extracted by
the caller into a BakeInputs before reaching this module.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Type

import numpy as np

from .specs import TempInitSpec, UniformTempSpec, WeightPaintedTempSpec


@dataclass(frozen=True)
class BakeInputs:
    """ Raw numeric context a strategy's evaluate() may need, already
    extracted from bpy state by the caller.

    :param vertex_count: number of vertices on the mesh being baked.
    :param vertex_group_weights: per-vertex weights (0-1), aligned by index
        to the mesh's vertices. None if not applicable (e.g. for specs that
        don't need it) or not yet extracted.
    """
    vertex_count: int
    vertex_group_weights: Optional[np.ndarray] = None

