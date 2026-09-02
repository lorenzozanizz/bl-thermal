"""
Shader construction for thermal rendering.
"""

from ..thermal_core.contracts import ShadingType, TerminalMode
from .visualize import build_temperature_node_graph
from .transfer import TransferDescriptor, TransferNodeRegistry, RBFOTransfer
from .emissivity import build_apparent_signal
from .terminal import build_terminal, signal_span
from .palette import apply_thermal_palette
from .properties import RBFOTransferProperties

__all__ = (
    "ShadingType",
    "TerminalMode",
    "build_temperature_node_graph",
    "TransferDescriptor",
    "TransferNodeRegistry",
    "RBFOTransfer",
    "build_apparent_signal",
    "build_terminal",
    "signal_span",
    "apply_thermal_palette",
    "RBFOTransferProperties",
)

# PropertyGroups owned by this package, consumed by the addon's registration
# tuple. Transfer parameter groups must register before any group pointing at
# them.
classes = (
    RBFOTransferProperties,
)
