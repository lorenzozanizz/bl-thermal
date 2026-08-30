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


# Typing hint
# A function which gets evaluated for a temperature initialziation
# specification and produces the correct mesh temperature field
EvaluateFn = Callable[[TempInitSpec, BakeInputs], np.ndarray]


class BakeStrategyRegistry:
    """ Maps a TempInitSpec subclass to the pure function that evaluates it
    into a per-vertex float64 Kelvin array.

    Adding a new strategy's numeric side means: (1) a dataclass in specs.py
    (already done for GRADIENT/AMBIENT at the InitType level, once their
    TempInitSpec subclasses exist), (2) one @register(SpecType) function
    here. Callers never branch on spec type directly - always through
    evaluate().
    """

    _REGISTRY: Dict[Type[TempInitSpec], EvaluateFn] = {}

    @classmethod
    def register(cls, spec_type: Type[TempInitSpec]):
        def decorator(fn: EvaluateFn) -> EvaluateFn:
            cls._REGISTRY[spec_type] = fn
            return fn
        return decorator

    @classmethod
    def evaluate(cls, spec: TempInitSpec, inputs: BakeInputs) -> np.ndarray:
        """ Evaluate spec into a (inputs.vertex_count,) float64 array of
        Kelvin values.

        :param spec: resolved, already-validated TempInitSpec (see
            ui/resolution.py:SpecsResolver.resolve_object_spec).
        :param inputs: numeric context extracted from bpy by the caller.
        :raises NotImplementedError: spec's type has no evaluator registered
            yet (e.g. a future GradientTempSpec/AmbientTempSpec).
        """
        try:
            fn = cls._REGISTRY[type(spec)]
        except KeyError:
            raise NotImplementedError(
                f"{type(spec).__name__!r} has no BakeStrategyRegistry "
                f"evaluator registered yet."
            ) from None
        return fn(spec, inputs)


# Type hint
# A function which re-parametrizes the 0-1 weights falloff in some way, ensuring
# the range is still [0, 1]
FalloffStrategy = Callable[[np.ndarray], np.ndarray]

class FalloffFunctions:

    @staticmethod
    def _smoothstep(t: np.ndarray) -> np.ndarray:
        """ Classic 3t^2 - 2t^3 smoothstep. """
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def evaluate(weights: np.ndarray, falloff_type: str) -> np.ndarray:
        """

        :param weights:
        :param falloff_type:
        :return:
        """
        eval_fn = {
            "LINEAR": lambda s, i: i.vertex_group_weights,
            "EASE_IN_OUT": FalloffFunctions._smoothstep,
        }.get(falloff_type, lambda t: t)
        return eval_fn(weights)


@BakeStrategyRegistry.register(UniformTempSpec)
def _evaluate_uniform(spec: UniformTempSpec, inputs: BakeInputs) -> np.ndarray:
    """ Every vertex gets the same value and vertex_group_weights is unused. """
    return np.full(inputs.vertex_count, spec.value_k, dtype=np.float64)


@BakeStrategyRegistry.register(WeightPaintedTempSpec)
def _evaluate_weight_painted(spec: WeightPaintedTempSpec, inputs: BakeInputs) -> np.ndarray:
    """ Remaps inputs.vertex_group_weights (0-1) onto [spec.min_k, spec.max_k]
    through the specified falloff function spec.falloff.

    :raises ValueError: vertex_group_weights is missing/wrong length
    """
    weights = inputs.vertex_group_weights
    if weights is None:
        raise ValueError(
            "WeightPaintedTempSpec requires BakeInputs.vertex_group_weights, "
            "got None - the caller must extract the named vertex group's "
            "weights before calling evaluate()."
        )

    weights = np.asarray(weights, dtype=np.float64)
    if weights.shape[0] != inputs.vertex_count:
        raise ValueError(
            f"vertex_group_weights length ({weights.shape[0]}) does not "
            f"match vertex_count ({inputs.vertex_count})"
        )

    clamped = np.clip(weights, 0.0, 1.0)
    t = FalloffFunctions.evaluate(clamped, spec.falloff)
    return spec.min_k + t * (spec.max_k - spec.min_k)