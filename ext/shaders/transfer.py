"""
Builds a radiometric transfer as a Cycles/EEVEE node chain.

A descriptor takes an input socket carrying Kelvin and returns an output
socket carrying signal. This is supposed to be general to allow different transfers
depending on camera model / realism etc...
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Type

from bpy.types import NodeSocket, PropertyGroup, ShaderNodeTree, UILayout

from ..thermal_core.contracts import TransferType
from ..thermal_core.radiometry import (
    MIN_TRANSFER_TEMPERATURE_K, RBFOTransferSpec, TransferSpec,
)
from .properties import RBFOTransferProperties



class TransferDescriptor(ABC):
    """ Everything needed to work with one transfer at the bpy layer.

    :param transfer_type: the TransferType this descriptor implements.
    :param property_group: PropertyGroup class holding its parameters.
    :param attr_name: attribute name the group lives under on the settings
        group that owns it.
    """
    transfer_type: TransferType
    property_group: Type[PropertyGroup]
    attr_name: str

    @staticmethod
    @abstractmethod
    def draw(layout: UILayout, props: PropertyGroup) -> None:
        """ Draw this descriptor in the UI, with its editable properties. """
        pass

    @staticmethod
    @abstractmethod
    def build_spec(props: PropertyGroup) -> TransferSpec:
        pass

    @staticmethod
    @abstractmethod
    def build_nodes(
        tree: ShaderNodeTree,
        temperature_socket: NodeSocket,
        props: PropertyGroup,
        location: Tuple[float, float],
    ) -> NodeSocket:
        """ Append this transfer's nodes to tree and return the socket carrying
        the resulting transformed signal (a function of a raw temperature map across the scene).

        :param tree: node tree to append into.
        :param temperature_socket: input socket supplying Kelvin temperature map.
        :param props: parameter group for this transfer.
        :param location: top-left position for the generated chain (for visual inspection).
        """
        pass


class TransferNodeRegistry:
    """ Maps a TransferType to its TransferDescriptor.
    Keyed on the TransferType enum.
    """

    _REGISTRY: Dict[TransferType, Type[TransferDescriptor]] = {}

    @classmethod
    def register(cls, transfer_type: TransferType):
        def decorator(descriptor: Type[TransferDescriptor]) -> Type[TransferDescriptor]:
            cls._REGISTRY[transfer_type] = descriptor
            return descriptor
        return decorator

    @staticmethod
    def get(transfer_type: TransferType) -> Type[TransferDescriptor]:
        """ Look up a descriptor.

        :raises NotImplementedError: if transfer_type is declared in TransferType
            but has no descriptor yet.
        """
        try:
            return TransferNodeRegistry._REGISTRY[transfer_type]
        except KeyError:
            raise NotImplementedError(
                f"{transfer_type!r} has no TransferDescriptor registered yet."
            ) from None

    @staticmethod
    def implemented() -> Tuple[Type[TransferDescriptor], ...]:
        """ Descriptors with a working implementation for populating the UI. """
        return tuple(TransferNodeRegistry._REGISTRY.values()) # type: ignore
        # ^ I dont know why the IDE highlights this wrong.

    @staticmethod
    def is_implemented(transfer_type: TransferType) -> bool:
        return transfer_type in TransferNodeRegistry._REGISTRY


class MathCompositor:
    """ Appends Math nodes left to right, tracking position and current output.

    Each operand is either a float or a NodeSocket, and finishes inside the given
    input index.

    The class composes the computation tree in steps, at each step taking track
    of which node was just added and inserting after it.
    """

    def __init__(self, tree: ShaderNodeTree, location: Tuple[float, float], socket: NodeSocket):
        self._tree = tree
        # Initial offset of the tree in the composite editor
        self._x, self._y = location
        self.socket = socket

        # offset
        self.CONSTANT_OFFSET = 180

    def step(self, operation: str, operand, socket_index: int = 1, label: str = "") -> NodeSocket:
        """ Add one Math node consuming the current socket.

        :param operation: ShaderNodeMath operation, e.g. 'DIVIDE'
            Must be a valid operation in the Blender interface
            https://docs.blender.org/api/current/bpy_types_enum_items/node_math_items.html#rna-enum-node-math-items
        :param operand: float or NodeSocket for the other input.
        :param socket_index: input index the current socket occupies
        :param label: node label, shown in the shader editor
        """
        node = self._tree.nodes.new('ShaderNodeMath')
        node.operation = operation
        node.location = (self._x, self._y)
        node.label = label

        # This works because we assume the index is 0 or 1
        other_index = 1 - socket_index
        self._tree.links.new(self.socket, node.inputs[socket_index])
        if isinstance(operand, NodeSocket):
            self._tree.links.new(operand, node.inputs[other_index])
        else:
            node.inputs[other_index].default_value = operand

        # Insert a small horizontal step, this is only useful for direct inspection
        self._x += self.CONSTANT_OFFSET
        self.socket = node.outputs[0]
        return self.socket

    def step_unary(self, operation: str, label: str = "") -> NodeSocket:
        """ Add a single-input Math node, which reads input 0 only.

        :param operation: ShaderNodeMath operation, e.g. 'EXPONENT'. See this docs for
            step() to see the list of available operations.
        :param label: node label, shown in the shader editor.
        """
        node = self._tree.nodes.new('ShaderNodeMath')
        node.operation = operation
        node.location = (self._x, self._y)
        node.label = label

        self._tree.links.new(self.socket, node.inputs[0])

        # Insert a small horizontal step, this is only useful for direct inspection
        self._x += self.CONSTANT_OFFSET
        self.socket = node.outputs[0]
        return self.socket


@TransferNodeRegistry.register(TransferType.RBFO)
class RBFOTransfer(TransferDescriptor):
    """ S = R / (exp(B/T) - F) + O, as seven Math nodes.

    Every operation is GPU-native in both Cycles and EEVEE, and the parameters
    stay live-editable without regenerating the tree.
    """

    transfer_type = TransferType.RBFO
    property_group = RBFOTransferProperties
    attr_name = "rbfo"

    # Largest exponent argument passed to a Math EXPONENT node. Shader math is
    # float32, which overflows past about an exponent of 90.
    MAX_EXPONENT_ARGUMENT = 80.0

    @staticmethod
    def draw(layout: UILayout, props: RBFOTransferProperties) -> None:
        column = layout.column(align=True)
        column.prop(props, "r")
        column.prop(props, "b")
        column.prop(props, "f")
        column.prop(props, "o")

    @staticmethod
    def build_spec(props: RBFOTransferProperties) -> RBFOTransferSpec:
        return RBFOTransferSpec(r=props.r, b=props.b, f=props.f, o=props.o)

    @staticmethod
    def build_nodes(
        tree: ShaderNodeTree,
        temperature_socket: NodeSocket,
        props: RBFOTransferProperties,
        location: Tuple[float, float],
    ) -> NodeSocket:
        chain = MathCompositor(tree, location, temperature_socket)

        # Guard the division, matching the clamp the numpy evaluator applies.
        chain.step('MAXIMUM', MIN_TRANSFER_TEMPERATURE_K, label="Clamp T")
        # B / T, with B in input 0.
        chain.step('DIVIDE', props.b, socket_index=1, label="B / T")
        # this applies min(const, exponent)
        chain.step('MINIMUM', RBFOTransfer.MAX_EXPONENT_ARGUMENT, label="Clamp exponent")
        chain.step_unary('EXPONENT', label="exp")
        chain.step('SUBTRACT', props.f, socket_index=0, label="- F")
        # F > 1 admits a zero denominator so keep it one-sided.
        # this takes max(F, 1e-6) to avoid underflow of the denominator
        chain.step('MAXIMUM', 1e-6, label="Guard denominator")
        # R / denominator, with R in input 0.
        chain.step('DIVIDE', props.r, socket_index=1, label="R / denom")
        return chain.step('ADD', props.o, socket_index=0, label="+ O")
