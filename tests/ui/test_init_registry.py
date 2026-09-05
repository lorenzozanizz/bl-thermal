from types import SimpleNamespace

import pytest

from ext.thermal_core.contracts import InitType, SpecScope
from ext.thermal_core.specs import UniformTempSpec, WeightPaintedTempSpec
from ext.ui.init_registry import InitStrategyRegistry


def test_get_strategy_inherit_raises_value_error():
    # INHERIT is a resolution-time concept, not a strategy with its own
    # params - see resolution.py for what actually handles it.
    with pytest.raises(ValueError):
        InitStrategyRegistry.get_strategy(InitType.INHERIT)



def test_strategies_for_scope_excludes_weight_painted_at_collection():
    obj_types = {d.init_type for d in InitStrategyRegistry.strategies_for_scope(SpecScope.OBJECT)}
    coll_types = {d.init_type for d in InitStrategyRegistry.strategies_for_scope(SpecScope.COLLECTION)}

    assert InitType.WEIGHT_PAINTED in obj_types
    assert InitType.WEIGHT_PAINTED not in coll_types
    assert InitType.INHERIT not in obj_types  # never a registry entry


def test_uniform_build_spec_converts_celsius_to_kelvin():

    props = SimpleNamespace(value=25.0, unit="CELSIUS")
    spec = InitStrategyRegistry.get_strategy(InitType.UNIFORM).build(props)

    assert isinstance(spec, UniformTempSpec)
    assert spec.value_k == pytest.approx(298.15)


def test_weight_painted_build_spec_converts_celsius_to_kelvin():

    props = SimpleNamespace(vertex_group="hot", min_value=20.0, max_value=60.0,
                             unit="CELSIUS", falloff="LINEAR")
    spec = InitStrategyRegistry.get_strategy(InitType.WEIGHT_PAINTED).build(props)

    assert isinstance(spec, WeightPaintedTempSpec)
    assert spec.min_k == pytest.approx(293.15)
    assert spec.max_k == pytest.approx(333.15)


def test_draw_touches_expected_property_fields():

    class FakeLayout:
        def __init__(self):
            self.fields = []

        def prop(self, data, field_name):
            self.fields.append(field_name)

    layout = FakeLayout()
    InitStrategyRegistry.get_strategy(
        InitType.UNIFORM).draw(layout, SimpleNamespace(value=1, unit="CELSIUS"))
    assert layout.fields == ["value", "unit"]