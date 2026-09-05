"""
Bpy-facing orchestration for baking each mesh object's resolved
temperature-initialization spec into a per-vertex float mesh attribute.

This module is one half of the bpy boundary: it reads bpy state and turns it
into the plain arrays thermal_core understands (MeshSample), then writes the
resulting numbers back onto the mesh. Everything between those two points is
bpy-free and separately testable.
"""

from enum import Enum, auto
from typing import List, Optional, Tuple

import numpy as np
from bpy.types import Operator, Object

from .names import Labels
from ..constants import (
    TEMPERATURE_ATTR_NAME, TEMPERATURE_ATTR_TYPE, TEMPERATURE_ATTR_DOMAIN,
)
from ..thermal_core.baking import BakeStrategyRegistry
from ..thermal_core.field import MeshSample
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


class MeshSampler:
    """ Extracts a bpy Object's geometry into a bpy-free MeshSample.

    Baking, diffusing and evolving all begin by sampling the scene the same way.
    """

    @staticmethod
    def extract_vertex_group_weights(obj: Object, vertex_group_name: str) -> np.ndarray:
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
    def extract_positions(obj: Object) -> np.ndarray:
        """ Reads obj's vertex coordinates into an (N, 3) float64 array in
        WORLD space.

        Blender stores coordinates in object-local space, so the object's
        world matrix is applied here. See the note in thermal_core/field.py:
        operations that read two objects at once need a shared frame, and
        converting here means each of them does not have to.
        """
        mesh = obj.data
        vertex_count = len(mesh.vertices)

        flat = np.empty(vertex_count * 3, dtype=np.float64)
        mesh.vertices.foreach_get('co', flat)
        local = flat.reshape(vertex_count, 3)

        # matrix_world is a 4x4 row-major affine transform; world = R @ p + t.
        matrix = np.array(obj.matrix_world, dtype=np.float64)
        rotation_scale = matrix[:3, :3]
        translation = matrix[:3, 3]
        return local @ rotation_scale.T + translation

    @staticmethod
    def extract_edges(obj: Object) -> np.ndarray:
        """ Reads obj's edges into an (E, 2) int32 array of vertex indices.

        Undirected, each edge listed once, exactly as Blender stores it.
        MeshSample.adjacency() is what turns this into a neighbour lookup.
        """
        mesh = obj.data
        edge_count = len(mesh.edges)

        flat = np.empty(edge_count * 2, dtype=np.int32)
        mesh.edges.foreach_get('vertices', flat)
        return flat.reshape(edge_count, 2)

    @staticmethod
    def sample(obj: Object, vertex_group_name: Optional[str] = None) -> MeshSample:
        """ Build the complete MeshSample for one mesh object.

        :param obj: a MESH object. Callers are expected to have filtered by
            type already.
        :param vertex_group_name: name of the vertex group whose weights the
            resolved spec needs, or None when it needs none. Weights are only
            read when asked for, since the loop is the expensive part of
            sampling and most strategies never look at it.
        :raises KeyError: vertex_group_name was given but obj has no such group.
        """
        weights = (
            None if vertex_group_name is None
            else MeshSampler.extract_vertex_group_weights(obj, vertex_group_name)
        )
        return MeshSample(
            vertex_count=len(obj.data.vertices),
            positions=MeshSampler.extract_positions(obj),
            edges=MeshSampler.extract_edges(obj),
            vertex_group_weights=weights,
        )


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

        # The rest just verifies if any bake procedure has gone wrong, and warns the user
        # accordingly
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
                attribute.data_type != TEMPERATURE_ATTR_TYPE
                or attribute.domain != TEMPERATURE_ATTR_DOMAIN)):
            # This implements
            raise RuntimeError(
                f"{obj.name!r} already has an attribute named {TEMPERATURE_ATTR_NAME!r} of type "
                f"{attribute.data_type!r} on the {attribute.domain!r} domain, but the temperature field needs "
                f"{TEMPERATURE_ATTR_TYPE!r} on {TEMPERATURE_ATTR_DOMAIN!r}. "
                f"Rename or remove the conflicting attribute."
            )
        if attribute is None:
            attribute = mesh.attributes.new(
                name=TEMPERATURE_ATTR_NAME,
                type=TEMPERATURE_ATTR_TYPE,
                domain=TEMPERATURE_ATTR_DOMAIN,
            )
        # foreach_set takes the fast path only when the array's dtype matches
        # the attribute's storage. The core computes in float64 for accuracy
        # during iterative operations; the narrowing happens here, once, at the
        # point where the values stop being numbers and become mesh data.
        attribute.data.foreach_set('value', np.ascontiguousarray(values, dtype=np.float32))
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

        # Create a BPY-agnostic object so that we can decouple the backend to
        # test it separately
        try:
            sample = MeshSampler.sample(obj, spec.get_vertex_group())
        except KeyError:
            return BakeOutcome.SKIPPED_MISSING_VERTEX_GROUP

        try:
            values = BakeStrategyRegistry.evaluate(spec, sample)
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
