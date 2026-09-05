"""
The complete bpy-independent description of how a scene's temperature field is
produced. There is one initial source spec per object, plus a scene-wide ordered list of
operations applied afterwards to objects and groups of objects.

"""

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Dict, Mapping, Tuple
from enum import Enum

from .field import ObjectKey
from .specs import TempInitSpec


# The pipeline treats operations opaquely and defers to an injected applier, so
# nothing here needs the concrete type yet.
FieldOperation = Any


class ConfigError(Exception):
    """ Raised when a SceneThermalConfig is structurally invalid. Depends on the config type.  """




@dataclass(frozen=True)
class SceneThermalConfig:
    """ Every object's source strategy, and the operations run over the result

    :param sources: object key -> the resolved spec that creates its field. In this way an object
        absent from this mapping is not baked at all.
    :param operations: applied in order after every source has been evaluated
    """

    sources: Mapping[ObjectKey, TempInitSpec] = field(default_factory=dict)
    operations: Tuple[FieldOperation, ...] = ()

    def keys(self) -> Tuple[ObjectKey, ...]:
        """ Object keys in a stable order, so bakes are reproducible. """
        return tuple(self.sources.keys())

    def validate(self) -> None:
        """ Validate every source spec and every operation.

        :raises ConfigError: any member fails its own validate().
        """
        # Note that this exceptions are not propagated to Blender, they are intercepted
        # by the UI layer and presented.
        for key, spec in self.sources.items():
            try:
                spec.validate()
            except ValueError as error:
                raise ConfigError(f"Source spec for {key!r} is invalid: {error}") from error

        for index, operation in enumerate(self.operations):
            validate = getattr(operation, "validate", None)
            if validate is None:
                continue
            try:
                validate()
            except ValueError as error:
                raise ConfigError(f"Operation {index} is invalid: {error}") from error

    def only_init(self, sources: Mapping[ObjectKey, TempInitSpec]) -> "SceneThermalConfig":
        """ A copy carrying different sources and the same operations. """
        return SceneThermalConfig(sources=dict(sources), operations=self.operations)

    def only_ops(self, operations: Tuple[FieldOperation, ...]) -> "SceneThermalConfig":
        """ A copy carrying different operations and the same sources. """
        return SceneThermalConfig(sources=dict(self.sources), operations=tuple(operations))

    def to_dict(self) -> Dict[str, Any]:
        """ Convert to plain JSON (dictionary) data.

        Each entry records its class name alongside its fields, which is what
        from_dict uses to pick the class to rebuild when its needed.
        """
        # Simply enumerate all operatiosn and initializations.
        return {
            "sources": {
                key: _tagged(spec) for key, spec in self.sources.items()
            },
            "operations": [_tagged(operation) for operation in self.operations],
        }

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> "SceneThermalConfig":
        """ Rebuild a config produced by to_dict.

        Operations are not rebuilt yet; the operation registry arrives in
        phase 3 and will supply the class lookup.

        :raises ConfigError: the data is malformed or names an unknown spec.
        """
        raw_sources = data.get("sources", {})
        if not isinstance(raw_sources, Mapping):
            raise ConfigError("'sources' must be a mapping of object key to spec")

        sources: Dict[ObjectKey, TempInitSpec] = {}
        for key, entry in raw_sources.items():
            try:
                spec_class = TempInitSpec.named(entry["type"])
                # Construct the required type. This allows to serialize
                # and deserialize scene configs.
                sources[key] = spec_class(**entry.get("params", {}))
            except (KeyError, TypeError) as error:
                raise ConfigError(
                    f"Could not rebuild the source spec for {key!r}: {error}"
                ) from error

        return SceneThermalConfig(sources=sources)


def _tagged(item: Any) -> Dict[str, Any]:
    """ A dataclass as {"type": class name, "params": its fields}. """
    if not is_dataclass(item):
        raise ConfigError(f"{type(item).__name__} is not a dataclass and cannot be serialized")
    return {"type": type(item).__name__, "params": asdict(item)}
