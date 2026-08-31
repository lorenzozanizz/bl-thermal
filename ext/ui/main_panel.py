"""
Panel classes and composable UISections for the extension's UI.

"""

from abc import abstractmethod, ABCMeta
from typing import Callable, Iterable, Optional

from bpy.types import Panel, Context, ID, Object, Collection

from ..operators.names import Labels
from ..constants import *
from ..thermal_core.contracts import InitType, SpecScope
from .init_registry import InitStrategyRegistry
from .resolution import SpecsResolver, SpecResolutionError


class UISection(metaclass=ABCMeta):
    """ A self-contained, composable piece of panel UI. """

    @abstractmethod
    def draw(self, context: Context, layout) -> None:
        """ Draw this section's contents into "layout" """
        raise NotImplementedError


class BakeSection(UISection):
    """ A section containing all options and buttons pertaining to
    scene baking, including specification resolution outputs and the
    baking itself.

    Includes a count and warnings about spec resolutions in the hierarchy.
    """

    @staticmethod
    def _count_ready(context: Context) -> tuple[int, int]:
        ready = 0
        total_mesh = 0
        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue
            total_mesh += 1
            try:
                spec = SpecsResolver.resolve_object_spec(obj)
                spec.validate()
            except (SpecResolutionError, NotImplementedError, ValueError):
                continue
            ready += 1
        return ready, total_mesh

    def draw(self, context: Context, layout) -> None:
        ready, total_mesh = 1, 2# self._count_ready(context)

        if total_mesh == 0:
            layout.label(text="No mesh objects in scene", icon='INFO')
        else:
            layout.label(
                text=f"{ready}/{total_mesh} mesh object(s) ready to bake",
                icon='CHECKMARK' if ready == total_mesh else 'INFO',
            )

        layout.operator(
            Labels.BAKE_TEMPERATURE.value,
            text="Bake Initial Temperature",
            icon='RENDER_STILL',
        )


class SpecSection(UISection):
    """ Draws the temperature-init strategy dropdown and the active
    strategy's parameters for a single scoped target.

    A single class serves both Object and Collection scope (rather than two
    near-duplicate classes) - `scope` and `get_target` are supplied at
    construction time by whichever Panel is using it (see MainPanel /
    CollectionSpecPanel below).
    """

    def __init__(self, scope: SpecScope, get_target: Callable[[Context], Optional[ID]]):
        self._scope = scope
        self._get_target = get_target

    def draw(self, context: Context, layout) -> None:
        target = self._get_target(context)
        if target is None:
            layout.label(text=f"No active {self._scope.value.lower()}", icon='INFO')
            return

        strategy_props = target.thermal_init
        layout.prop(strategy_props, "init_type")

        init_type = InitType[strategy_props.init_type]

        if init_type is InitType.INHERIT:
            # Resolving what INHERIT actually evaluates to
            layout.label(text="Inherits from collection default", icon='INFO')
            return

        try:
            descriptor = InitStrategyRegistry.get_strategy(init_type)
        except NotImplementedError:
            layout.label(text=f'"{init_type.value}" is not implemented yet', icon='ERROR')
            return

        sub_props = getattr(strategy_props, descriptor.attr_name)
        descriptor.draw(layout, sub_props)


class RenderSection(UISection):
    """ Placeholder """

    def draw(self, context: Context, layout) -> None:
        pass


class CentralPanel(UISection):
    """ Composes an ordered sequence of UISections into one draw() call each in its own box.
    This constructs the central panel holding generation information and (to be determined)
    hooks.
    """

    def __init__(self, sections: Iterable[UISection]):
        self._sections = tuple(sections)

    def draw(self, context: Context, layout) -> None:
        for section in self._sections:
            section.draw(context, layout.box())

class MainPanel(Panel):
    """  """
    bl_idname = "THERMAL_PT_main"
    bl_label = "Thermal"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = MAIN_PANEL_NAME

    def draw(self, context: Context) -> None:
        panel = CentralPanel(sections=[
            SpecSection(scope=SpecScope.OBJECT, get_target=lambda ctx: ctx.object),
            BakeSection(),
        ])
        panel.draw(context, self.layout)


class CollectionSpecPanel(Panel):
    """ Properties Editor tab (shown when a Collection is the active
    outliner ID) for setting a collection's default initial temperature.
    """
    bl_idname = "THERMAL_PT_collection_spec"
    bl_label = "Thermal"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "collection"

    def draw(self, context: Context) -> None:
        panel = CentralPanel(sections=[
            SpecSection(scope=SpecScope.COLLECTION, get_target=lambda ctx: ctx.collection),
        ])
        panel.draw(context, self.layout)


class InfoPanel(Panel):

    bl_idname = "THERMAL_PT_info"
    bl_label = "Info"
    bl_category = MAIN_PANEL_NAME
    bl_options = { 'DEFAULT_CLOSED' }
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_order = 4

    def draw(self, context):

        layout = self.layout

        # Title
        col = layout.column(align=True)
        col.label(text=MAIN_PANEL_NAME, icon='INFO')
        col.separator()

        # Version Info
        col.label(text=f"Version: {VERSION}")
        col.label(text=f"Tested on Blender {TARGET_VERSION}")
        col.separator()

        # Links section
        col = layout.column(align=True)
        col.label(text="Links:")

        row = col.row()
        op = row.operator(Labels.OPEN_URL.value, text="GitHub", icon='URL')
        op.url = REPO_URL
        op = row.operator(Labels.OPEN_URL.value, text="Documentation", icon='FILE_FOLDER')
        op.url = DOCU_URL