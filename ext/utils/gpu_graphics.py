"""



"""
from typing import Union



def resolve_color(color: Union[str, tuple]) -> tuple:
    """

    :param color:
    :return:
    """

    if isinstance(color, str):
        return {
            "yellow": (0, 0, 0)
        }.get(color, (0.5, 0.5, 0.5))
    else:
        return color

def draw_outline(color: Union[str, tuple] = "yellow"):
    """ Draws the outline of an object around said object in the viewport so that the
    user can visualize which items are currently selected. """

    color = resolve_color(color)
    pass