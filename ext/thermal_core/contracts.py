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

class ShadingType(Enum):
    """ Machinery used to evaluate a transfer and turn it into an image.

    Orthogonal to TransferType, which is the physics. NODE_SHADER and
    RAY_NODE_SHADER can run identical radiometry and still produce different
    images, because only one of them traces reflections.
    """
    # Use geometric/graphical nodes to construct the correct shader using
    # Cycles default ray tracing capabilities
    RAY_NODE_SHADER = "Ray Node Shader"
    # Same, but use OSL (can only work on GPU for OptiX
    RAY_OSL_SHADER = "Ray OSL Shader"

    # Use nodes to perform a scalar mapping, no ray tracing
    NODE_SHADER = "Node Shader"
    # Try to attempt a numpy per-pixel emittance computation
    NUMPY_SHADER = "NumPy Shader"

    # Custom implementation of ray shaders, potentially very slow.
    MANUAL_RAY = "Custom Ray"

    # Just emit a temperature map for the scene
    TEMPERATURE_SHADER = "Temperature Shader"

    def uses_transfer(self) -> bool:
        """ Whether this path can use transfer functions to normalize
        """
        return self is not ShadingType.TEMPERATURE_SHADER


class TerminalMode(Enum):
    """ What the end of a shader graph produces. """

    # The quantitative emissivity to be used for EXR output
    RAW = "Raw Signal"
    # Signal normalized and run through a palette. Used only for
    # viewport visualization of the baked temperature / emission map
    FALSE_COLOR = "False Color"


class ThermographyType(Enum):
    """

    """
    TEMPERATURE = "Temperature"
    RADIANCE = "Radiance"
    RAYTRACE = "Raytrace"


class TransferType(Enum):
    """ Radiometric transfer function used to turn a surface temperature into
    a sensor signal.

    A thermal camera does not measure temperature but measures radiated power
    inside a finite waveband and infers a temperature from it, up to the problem of
    emissivity.

    The transfer type is the law which maps from temperature to raw radiated power, before
    applying emissivity reduction.
    """

    # S = R / (exp(B/T) - F) + O. A narrow-band reduction of Planck's law,
    #   and the calibration form real LWIR cameras ship their constants in.
    # Taken from
    # https://device.report/m/bb0fb3a133c0e28de013f89093d51f0629ef0e14866976b11b9d92bc19177b85.pdf
    # GenICam ICD FLIR AX5 Camera
    RBFO = "Calibration (R/B/F/O)"

    # Planck's law multiplied by the sensor's spectral response and
    # integrated across the band, precomputed into a lookup table.
    PLANCK_LUT = "Band-integrated Planck"

    # M = eps*sigma*T^4. Total radiated power across all wavelengths, from
    # reference \cite{waldermar_et_dudzik}
    STEFAN_BOLTZMANN = "Stefan-Boltzmann"