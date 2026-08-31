"""
Bpy-facing orchestration for visualizing the baked per-vertex temperature
attribute as material color.

Builds one shared material, scaled to the combined min/max across every
baked object, and assigns it to each so the color scale is comparable
across the entire scene.
"""

from typing import List, Optional

import bpy
import numpy as np
from bpy.types import Operator, Object, Material

from .names import Labels
from ..constants import TEMPERATURE_ATTR_NAME, TEMPERATURE_MATERIAL_NAME
from ..shaders.visualize import build_temperature_node_graph


class VisualizeTemperatureOperator(Operator):
    """ Builds/updates the single shared TEMPERATURE_MATERIAL_NAME material
    scaled to the min/max across every baked mesh object's TEMPERATURE_ATTR_NAME values,
    and assigns it to material slot 0 on each of those objects.

    """
    bl_idname = Labels.VISUALIZE_TEMPERATURE.value
    bl_label = "Visualize Temperature"
    bl_description = (
        "Color every baked object by its temperature attribute, using a "
        "shared min/max scale across the scene"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects_iter = VisualizeTemperatureOperator._iter_baked_mesh_objects(context)
        if not objects_iter:
            self.report({'WARNING'}, "No baked temperature data found, run Bake first")
            return {'CANCELLED'}

        combined = np.concatenate(
            [VisualizeTemperatureOperator._read_temperature_values(obj) for obj in objects_iter]
        )
        min_value = float(combined.min())
        max_value = float(combined.max())

        if abs(min_value - max_value) < 1e-3:
            # Degenerate range. Pad symmetrically so it still resolves to one
            # consistent mid-ramp color instead of undefined behaviour.
            min_value -= 0.5
            max_value += 0.5

        material = VisualizeTemperatureOperator._get_or_create_material()
        # Create the material corresponding to the node graph which extracts the temperature
        # fields and maps it onto a color ramp.
        build_temperature_node_graph(material, TEMPERATURE_ATTR_NAME, min_value, max_value)

        for obj in objects_iter:
            VisualizeTemperatureOperator._assign_material(obj, material)

        self.report(
            {'INFO'},
            f"Visualized {len(objects_iter)} object(s), range "
            f"{min_value:.1f}-{max_value:.1f}. Switch viewport shading to "
            f"Material Preview or Rendered to see it."
        )
        return {'FINISHED'}

    @staticmethod
    def _read_temperature_values(obj: Object) -> Optional[np.ndarray]:
        """ Reads TEMPERATURE_ATTR_NAME off obj's mesh into a numpy array, or
        None if the object has no such attribute (i.e. hasn't been baked).
        """
        attribute = obj.data.attributes.get(TEMPERATURE_ATTR_NAME)
        if attribute is None:
            return None
        values = np.empty(len(obj.data.vertices), dtype=np.float64)
        attribute.data.foreach_get('value', values)
        return values

    @staticmethod
    def _iter_baked_mesh_objects(context) -> List[Object]:
        """ Every mesh object in the scene that has already been baked (see
        operators/baking.py:BakeTemperatureOperator). Objects never baked, or
        baked then reverted, are silently excluded rather than erroring - this
        operator visualizes what's there, it doesn't bake on the fly.
        """
        return [
            obj for obj in context.scene.objects
            if obj.type == 'MESH' and obj.data.attributes.get(TEMPERATURE_ATTR_NAME) is not None
        ]

    @staticmethod
    def _get_or_create_material() -> Material:
        material = bpy.data.materials.get(TEMPERATURE_MATERIAL_NAME)
        if material is None:
            material = bpy.data.materials.new(name=TEMPERATURE_MATERIAL_NAME)
        return material

    @staticmethod
    def _assign_material(obj: Object, material: Material) -> None:
        """ Ensures material occupies slot 0 on obj which
        renders by default, since faces default to material_index 0.
        """
        # TODO: Make this non-destructive.
        if len(obj.data.materials) == 0:
            obj.data.materials.append(material)
        else:
            obj.data.materials[0] = material
