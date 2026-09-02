"""
The end of a shader graph: what the apparent signal becomes on its way to
Material Output.

Two modes, and the distinction is the same one a radiometric camera makes.

RAW emits the linear signal untouched - no normalization, no clamping, no
palette. This is the measurement, and it is what gets written to an EXR. A
pixel value is a signal value, so it can be inverted back to Kelvin. Nothing
in this path may scale or clamp, or the output stops being data.

FALSE_COLOUR maps the signal through a palette for viewport inspection. The
span is supplied by the user in Kelvin and converted here with two scalar
evaluations of the transfer - the same "manual span" a camera offers. It is a
display choice, so it never applies to a file render.

Normalizing against a scene-wide min/max was deliberately rejected: it welds
a palette range into the material, makes every frame of a sequence scale to
itself, and destroys the recoverability of the underlying measurement.
"""

from typing import Tuple

import numpy as np
from bpy.types import Node, NodeSocket, PropertyGroup, ShaderNodeTree

from .nodes import MathCompositor
from ..thermal_core.contracts import TerminalMode
from ..thermal_core.radiometry import TransferRegistry, TransferSpec
from .palette import apply_thermal_palette


def signal_span(spec: TransferSpec, span_min_k: float, span_max_k: float) -> Tuple[float, float]:
    """ Convert a Kelvin display span into the corresponding signal span.

    :raises ValueError: the span is empty or inverted
    """
    if span_max_k <= span_min_k:
        raise ValueError(
            f"Display span is empty: min ({span_min_k}K) must be below max "
            f"({span_max_k}K)."
        )
    low, high = TransferRegistry.evaluate(spec, np.array([span_min_k, span_max_k]))
    # (This just computes the interval of values in the signal scale and not in the
    # temperature scale, assuming everytihng is monotonous etc...
    return float(low), float(high)


def build_terminal(
    tree: ShaderNodeTree,
    signal_socket: NodeSocket,
    settings: PropertyGroup,
    spec: TransferSpec,
    location: Tuple[float, float],
) -> None:
    """ Append the final material stage and connect it to a new Material Output.

    :param signal_socket: socket carrying apparent signal
    :param settings: the scene's ThermalRenderSettings
    :param spec: the transfer in use, needed to convert a Kelvin display span
    :param location: top-left of the generated block
    """
    mode = TerminalMode[settings.terminal_mode]
    x, y = location
    stride_x, _ = MathCompositor.strides()

    if mode is TerminalMode.FALSE_COLOR:
        shaded = _build_false_color(tree, signal_socket, settings, spec, (x, y))
        x += 2 * stride_x
    else:
        shaded = signal_socket

    emission: Node = tree.nodes.new('ShaderNodeEmission')
    emission.location = (x, y)
    emission.label = mode.value
    emission.inputs['Strength'].default_value = 1.0
    # A float socket linked into a colour socket broadcasts to (v, v, v) by blender
    # node compositing
    tree.links.new(shaded, emission.inputs['Color'])

    output: Node = tree.nodes.new('ShaderNodeOutputMaterial')
    output.location = (x + stride_x, y)
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])


def _build_false_color(
    tree: ShaderNodeTree,
    signal_socket: NodeSocket,
    settings: PropertyGroup,
    spec: TransferSpec,
    location: Tuple[float, float],
) -> NodeSocket:
    """ Map the signal onto the display span and through the palette. """
    low, high = signal_span(spec, settings.span_min_k(), settings.span_max_k())
    x, y = location
    stride_x, _ = MathCompositor.strides()

    map_range: Node = tree.nodes.new('ShaderNodeMapRange')
    map_range.location = (x, y)
    map_range.label = "Display span"
    # Clamped, so out-of-span reads saturate to the palette ends rather than
    # wrapping, basically we fix the extrema
    map_range.clamp = True
    map_range.inputs['From Min'].default_value = low
    map_range.inputs['From Max'].default_value = high
    map_range.inputs['To Min'].default_value = 0.0
    map_range.inputs['To Max'].default_value = 1.0
    tree.links.new(signal_socket, map_range.inputs['Value'])

    color_ramp: Node = tree.nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (x + stride_x, y)
    apply_thermal_palette(color_ramp.color_ramp)
    tree.links.new(map_range.outputs['Result'], color_ramp.inputs['Fac'])

    return color_ramp.outputs['Color']
