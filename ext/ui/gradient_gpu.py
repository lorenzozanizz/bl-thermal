""" 3D-viewport overlay for a GradientTempSpec: draws its two endpoints and
an arrow between them, pointing at the hotter one. """

from typing import Optional

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from ..thermal_core.specs import GradientTempSpec


class GradientOverlay:
    """ Persistent POST_VIEW draw handler for one GradientTempSpec at a time.

    Mirrors ColorBar's show/hide/toggle lifecycle (ui/color_bar_gpu.py), but
    draws in 3D world space (POST_VIEW) rather than 2D screen space
    (POST_PIXEL).
    """

    _POINT_COLOR = (1.0, 1.0, 1.0, 1.0)
    _LINE_COLOR = (1.0, 0.6, 0.0, 1.0)
    _POINT_SIZE = 10.0
    _ARROWHEAD_LENGTH = 0.15   # fraction of axis length
    _ARROWHEAD_WIDTH = 0.05    # world units

    def __init__(self) -> None:
        self._spec: Optional[GradientTempSpec] = None
        self._handle = None
        self._shader = gpu.shader.from_builtin("UNIFORM_COLOR")

    def is_active(self) -> bool:
        return self._handle is not None

    def show(self, spec: GradientTempSpec) -> None:
        """ Display (or update) the overlay for the given spec. """
        self._spec = spec
        if self._handle is None:
            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                self._draw, (), "WINDOW", "POST_VIEW",
            )
        self._tag_redraw()

    def hide(self) -> None:
        """ Remove the overlay. Explicitly deletes the drawing handler
        created during show(), matching ColorBar.hide(). """
        if self._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
            self._handle = None
        self._spec = None
        self._tag_redraw()

    def _draw(self) -> None:
        """ Draw callback. Should NOT be called externally, reserved for
        the draw handler. """
        if self._spec is None:
            return

        hot, cold = self._spec.hot_cold_points()
        hot, cold = Vector(hot), Vector(cold)

        gpu.state.point_size_set(self._POINT_SIZE)
        self._draw_points((hot, cold))
        self._draw_arrow(cold, hot)

    def _draw_points(self, points) -> None:
        batch = batch_for_shader(self._shader, "POINTS", {"pos": points})
        self._shader.bind()
        self._shader.uniform_float("color", self._POINT_COLOR)
        batch.draw(self._shader)

    def _draw_arrow(self, tail: Vector, tip: Vector) -> None:
        """ Shaft from tail to tip, plus a small flat arrowhead at tip. """
        gpu.state.line_width_set(2.0)
        shaft = batch_for_shader(self._shader, "LINES", {"pos": (tail, tip)})
        self._shader.bind()
        self._shader.uniform_float("color", self._LINE_COLOR)
        shaft.draw(self._shader)
        gpu.state.line_width_set(1.0)

        axis = tip - tail
        length = axis.length
        if length < 1e-9:
            return
        direction = axis / length

        # An arbitrary perpendicular vector, to fan the arrowhead out flat.
        perp = direction.cross(Vector((0.0, 0.0, 1.0)))
        if perp.length < 1e-6:
            perp = direction.cross(Vector((0.0, 1.0, 0.0)))
        perp.normalize()

        base = tip - direction * (length * self._ARROWHEAD_LENGTH)
        left = base + perp * self._ARROWHEAD_WIDTH
        right = base - perp * self._ARROWHEAD_WIDTH

        head = batch_for_shader(self._shader, "TRI_FAN", {"pos": (tip, left, right)})
        self._shader.bind()
        self._shader.uniform_float("color", self._LINE_COLOR)
        head.draw(self._shader)

    @staticmethod
    def _tag_redraw() -> None:
        """ Tags every 3D Viewport for redraw. Affects all viewports. """
        for window in bpy.context.window_manager.windows:
            screen = window.screen
            if screen is None:
                continue
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()


# Module-level singleton, same rationale as left_bottom_color_bar in
# ui/color_bar_gpu.py: the draw-handler reference has to live somewhere
# that survives across operator invocations.
gradient_overlay = GradientOverlay()
