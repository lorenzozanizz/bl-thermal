"""
False-colour palettes.
Display only.
"""

from bpy.types import ColorRamp

from ..constants import DEFAULT_HEAT_PALETTE


def apply_thermal_palette(color_ramp: ColorRamp) -> None:
    """ Overwrites color_ramp's stops with a cold(blue)->hot(red) palette """
    stops = (
        (0.00, DEFAULT_HEAT_PALETTE[0]),   # coldest: deep blue
        (0.33, DEFAULT_HEAT_PALETTE[1]),   # cool: cyan
        (0.66, DEFAULT_HEAT_PALETTE[2]),   # warm: yellow
        (1.00, DEFAULT_HEAT_PALETTE[3]),   # hottest: red
    )
    elements = color_ramp.elements
    elements[0].position, elements[0].color = stops[0]
    elements[-1].position, elements[-1].color = stops[-1]
    for position, color in stops[1:-1]:
        elements.new(position).color = color
