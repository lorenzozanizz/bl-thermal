"""
False-colour palettes.
Display only.
"""

from bpy.types import ColorRamp


def apply_thermal_palette(color_ramp: ColorRamp) -> None:
    """ Overwrites color_ramp's stops with a cold(blue)->hot(red) palette """
    stops = (
        (0.00, (0.0, 0.0, 0.6, 1.0)),   # coldest: deep blue
        (0.33, (0.0, 0.8, 0.8, 1.0)),   # cool: cyan
        (0.66, (1.0, 0.9, 0.0, 1.0)),   # warm: yellow
        (1.00, (0.8, 0.0, 0.0, 1.0)),   # hottest: red
    )
    elements = color_ramp.elements
    elements[0].position, elements[0].color = stops[0]
    elements[-1].position, elements[-1].color = stops[-1]
    for position, color in stops[1:-1]:
        elements.new(position).color = color
