from enum import Enum

from .visualize import *


class ShadingType(Enum):
    """

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