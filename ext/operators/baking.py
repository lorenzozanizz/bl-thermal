"""
Bpy-facing orchestration for baking each mesh object's resolved
temperature-initialization spec into a per-vertex float mesh attribute.

"""

from enum import Enum, auto
from typing import List, Optional, Tuple

import numpy as np
from bpy.types import Operator, Object

from .names import Labels
from ..constants import (
    TEMPERATURE_ATTR_NAME, TEMPERATURE_ATTR_TYPE, TEMPERATURE_ATTR_DOMAIN,
)
from ..thermal_core.baking import BakeInputs, BakeStrategyRegistry
from ..thermal_core.specs import WeightPaintedTempSpec
from ..ui.resolution import SpecsResolver, SpecResolutionError


class BakeOutcome(Enum):
    """ Per-object result of an attempted bake. Used to build
    BakeTemperatureOperator's end-of-run summary rather than reporting every object
    individually.
    """
    BAKED = auto()
    SKIPPED_NOT_MESH = auto()
    SKIPPED_UNRESOLVED = auto()
    SKIPPED_INVALID_SPEC = auto()
    SKIPPED_MISSING_VERTEX_GROUP = auto()
    SKIPPED_NOT_IMPLEMENTED = auto()


class BakeTemperatureOperator(Operator):
    """ Resolves every mesh object in the scene's effective temperature-init
    spec and bakes it into a per-vertex TEMPERATURE_ATTR_NAME float attribute
    (see constants.py).

    Objects that fail to resolve or use a not-yet-implemented strategy or
    reference a missing vertex group are skipped rather than blocking the entire
    scene bake.
    """
    bl_idname = Labels.BAKE_TEMPERATURE.value
    bl_label = "Bake Initial Temperature"
    bl_description = (
        "Resolve and bake every mesh object's initial-temperature spec "
        "into a per-vertex mesh attribute for shading"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        outcomes = [(obj, BakeTemperatureOperator._bake_one(obj)) for obj in context.scene.objects]

        any_baked = any(outcome is BakeOutcome.BAKED for _, outcome in outcomes)
        any_skipped_meaningfully = any(
            outcome not in (BakeOutcome.BAKED, BakeOutcome.SKIPPED_NOT_MESH)
            for _, outcome in outcomes
        )
        level = {'INFO'} if not any_skipped_meaningfully else {'WARNING'}
        self.report(level, self.make_summary(outcomes))

        if any_baked or not any_skipped_meaningfully:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

    @staticmethod
    def _extract_vertex_group_weights(obj: Object, vertex_group_name: str) -> np.ndarray:
        """ Reads vertex_group_name's per-vertex weight into an array aligned to
        obj.data.vertices. Vertices that aren't members of the group get 0.0,
        matching how weight-paint remapping treats "unpainted" as the bottom of
        the range.

        :raises KeyError: obj has no vertex group named vertex_group_name.
        """
        vertex_group = obj.vertex_groups[vertex_group_name]  # raises KeyError if absent
        # the vertex group has to have been created beforehand
        weights = np.zeros(len(obj.data.vertices), dtype=np.float64)
        # TODO: Optimize this loop somehow.
        for vertex in obj.data.vertices:
            try:
                weights[vertex.index] = vertex_group.weight(vertex.index)
            except RuntimeError:
                pass
        return weights

    @staticmethod
    def write_mesh_attribute(obj: Object, values: np.ndarray) -> None:
        """ Writes values (aligned to obj.data.vertices) into the
        TEMPERATURE_ATTR_NAME point-domain float attribute on obj's mesh,
        creating it if absent. Re-baking is idempotent: an existing attribute of
        the right type/domain is overwritten in place; one of the wrong
        type/domain is replaced.
        """
        mesh = obj.data
        attribute = mesh.attributes.get(TEMPERATURE_ATTR_NAME)
        if (attribute is not None and (
            # Ensure that we get the write attribute, if there is a conflict immediately
            # ensure the user is aware of that.
                attribute.data_type != TEMPERATURE_ATTR_TYPE
                or attribute.domain != TEMPERATURE_ATTR_DOMAIN)):
            raise RuntimeError("The mesh attribute corresponding to the temperature field over the "
                               "scene was already written. This could be due to a conflict of some sort.")
            # mesh.attributes.remove(attribute)
            # attribute = None
        if attribute is None:
            attribute = mesh.attributes.new(
                name=TEMPERATURE_ATTR_NAME,
                type=TEMPERATURE_ATTR_TYPE,
                domain=TEMPERATURE_ATTR_DOMAIN,
            )
        attribute.data.foreach_set('value', values)
        mesh.update()

    @staticmethod
    def _bake_one(obj: Object) -> BakeOutcome:
        """ Resolves, evaluates and writes the temperature bake for a single
        object.
        """
        if obj.type != 'MESH':
            return BakeOutcome.SKIPPED_NOT_MESH

        try:
            # Navigate the hierarchy and get a resolved specification
            spec = SpecsResolver.resolve_object_spec(obj)
        except SpecResolutionError:
            # Covers UnresolvedSpecError, AmbiguousInheritanceError and
            # InvalidCollectionSpecError, which are USER errors
            return BakeOutcome.SKIPPED_UNRESOLVED
        except NotImplementedError:
            # Resolved to a strategy with no StrategyDescriptor yet (so a not implemented one)
            return BakeOutcome.SKIPPED_NOT_IMPLEMENTED

        try:
            spec.validate()
        except ValueError:
            return BakeOutcome.SKIPPED_INVALID_SPEC

        vertex_group_weights: Optional[np.ndarray] = None
        if spec.get_vertex_group() is not None:
            try:
                vertex_group_weights = BakeTemperatureOperator._extract_vertex_group_weights(
                    obj, spec.get_vertex_group()
                )
            except KeyError:
                return BakeOutcome.SKIPPED_MISSING_VERTEX_GROUP

        # Create a BPY-agnostic object so that we can decouple the backend to
        # test it separately
        inputs = BakeInputs(
            vertex_count=len(obj.data.vertices),
            vertex_group_weights=vertex_group_weights,
        )

        try:
            values = BakeStrategyRegistry.evaluate(spec, inputs)
        except NotImplementedError:
            # A spec type with no BakeStrategyRegistry evaluator yet, we cant
            # do anything about it.
            return BakeOutcome.SKIPPED_NOT_IMPLEMENTED
        except ValueError:
            return BakeOutcome.SKIPPED_INVALID_SPEC

        BakeTemperatureOperator.write_mesh_attribute(obj, values)
        return BakeOutcome.BAKED

    @staticmethod
    def make_summary(outcomes: List[Tuple[Object, BakeOutcome]]) -> str:
        """ Builds the one-line final report for BakeTemperatureOperator,
        ignoring SKIPPED_NOT_MESH objects (cameras/lights/empties are expected
        to be present in every scene and aren't considered "skipped")
        """
        baked = sum(1 for _, outcome in outcomes if outcome is BakeOutcome.BAKED)
        skipped = [
            (obj, outcome) for obj, outcome in outcomes
            if outcome not in (BakeOutcome.BAKED, BakeOutcome.SKIPPED_NOT_MESH)
        ]

        if not skipped:
            return f"Baked {baked} object(s)"

        counts = {}
        for _, outcome in skipped:
            counts[outcome] = counts.get(outcome, 0) + 1
        detail = ", ".join(
            f"{count} {outcome.name.replace('SKIPPED_', '').replace('_', ' ').title()}"
            for outcome, count in counts.items()
        )
        return f"Baked {baked} object(s); skipped {len(skipped)}: {detail}"


class DiffuseTemperatureOperator(Operator):
    """ Modal operator to diffuse temperature across objects allowing potential UNDO capabilities.
    Not yet implemented
    """

    pass


class EvolveTemperatureOperator(Operator):
    """ Not yet implemented
    """
    pass