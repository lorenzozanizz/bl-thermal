"""
Shader construction for thermal rendering.
"""

from ..thermal_core.contracts import ShadingType, TerminalMode
from .registry import ShaderDescriptor, ShaderRegistry, NodeShader, TemperatureShader
from .transfer import TransferDescriptor, TransferNodeRegistry, RBFOTransfer
from .emissivity import build_apparent_signal
from .terminal import build_terminal
from .palette import apply_thermal_palette
from .properties import RBFOTransferProperties

__all__ = (
    "ShadingType",
    "TerminalMode",
    "ShaderDescriptor",
    "ShaderRegistry",
    "NodeShader",
    "TemperatureShader",
    "TransferDescriptor",
    "TransferNodeRegistry",
    "RBFOTransfer",
    "build_apparent_signal",
    "build_terminal",
    "apply_thermal_palette",
    "RBFOTransferProperties",
)

# Transfer parameter groups must register before any group pointing at them.
classes = (
    RBFOTransferProperties,
)
