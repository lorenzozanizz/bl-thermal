from types import SimpleNamespace

import pytest

from ext.thermal_core.specs import UniformTempSpec
from ext.ui.resolution import (
    AmbiguousInheritanceError,
    InvalidCollectionSpecError,
    UnresolvedSpecError,
    SpecsResolver,
)


def _strategy_props(init_type, **sub):
    """ Fake stand-in for an InitStrategyProperties instance (what real
    bpy. """
    return SimpleNamespace(
        init_type=init_type,
        uniform=SimpleNamespace(value=sub.get("value", 20.0), unit=sub.get("unit", "CELSIUS")),
        weight_painted=SimpleNamespace(
            vertex_group=sub.get("vertex_group", ""),
            min_value=sub.get("min_value", 0.0),
            max_value=sub.get("max_value", 0.0),
            unit=sub.get("unit", "CELSIUS"),
            falloff="LINEAR",
        ),
    )


def make_object(init_type, collections=(), **sub):
    return SimpleNamespace(name="Obj", thermal_init=_strategy_props(init_type, **sub),
                            users_collection=tuple(collections))


def make_collection(name, init_type, **sub):
    return SimpleNamespace(name=name, thermal_init=_strategy_props(init_type, **sub))


def test_concrete_object_strategy_resolves_without_touching_collections():
    obj = make_object("UNIFORM", value=25.0)
    spec = SpecsResolver.resolve_object_spec(obj)

    assert isinstance(spec, UniformTempSpec)
    assert spec.value_k == pytest.approx(298.15)


def test_inherit_resolves_through_single_collection():
    coll = make_collection("Coll", "UNIFORM", value=30.0)
    obj = make_object("INHERIT", collections=[coll])

    k_val = getattr(SpecsResolver.resolve_object_spec(obj), 'value_k')
    assert k_val == pytest.approx(303.15)


def test_inherit_with_no_concrete_collection_raises_unresolved():
    coll = make_collection("Coll", "INHERIT")
    obj = make_object("INHERIT", collections=[coll])

    with pytest.raises(UnresolvedSpecError):
        SpecsResolver.resolve_object_spec(obj)


def test_inherit_with_agreeing_collections_resolves():
    c1 = make_collection("A", "UNIFORM", value=25.0)
    c2 = make_collection("B", "UNIFORM", value=25.0)
    obj = make_object("INHERIT", collections=[c1, c2])

    k_val = getattr(SpecsResolver.resolve_object_spec(obj), 'value_k')
    assert k_val == pytest.approx(298.15)


def test_inherit_with_disagreeing_collections_raises_ambiguous():
    c1 = make_collection("A", "UNIFORM", value=25.0)
    c2 = make_collection("B", "UNIFORM", value=30.0)
    obj = make_object("INHERIT", collections=[c1, c2])

    with pytest.raises(AmbiguousInheritanceError):
        SpecsResolver.resolve_object_spec(obj)


def test_collection_with_illegal_scope_strategy_raises_invalid():
    # Simulates legacy/scripted data: WEIGHT_PAINTED stored on a Collection
    bad_coll = make_collection("Bad", "WEIGHT_PAINTED", vertex_group="hot", min_value=0, max_value=1)
    obj = make_object("INHERIT", collections=[bad_coll])

    with pytest.raises(InvalidCollectionSpecError):
        SpecsResolver.resolve_object_spec(obj)