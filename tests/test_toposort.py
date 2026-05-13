import pytest
from toposort import topo_sort, CycleError


def E(name):
    return {"name": name}


def R(frm, to, fk="x"):
    return {"from": frm, "to": to, "fk": fk}


def test_linear_chain():
    entities = [E("c"), E("a"), E("b")]
    relations = [R("b", "a"), R("c", "b")]
    result = [e["name"] for e in topo_sort(entities, relations)]
    assert result == ["a", "b", "c"]


def test_diamond():
    entities = [E("d"), E("a"), E("b"), E("c")]
    relations = [R("b", "a"), R("c", "a"), R("d", "b"), R("d", "c")]
    result = [e["name"] for e in topo_sort(entities, relations)]
    assert result.index("a") < result.index("b")
    assert result.index("a") < result.index("c")
    assert result.index("b") < result.index("d")
    assert result.index("c") < result.index("d")


def test_self_reference_allowed():
    entities = [E("emp")]
    relations = [R("emp", "emp", fk="manager_id")]
    result = [e["name"] for e in topo_sort(entities, relations)]
    assert result == ["emp"]


def test_cycle_raises():
    entities = [E("a"), E("b")]
    relations = [R("a", "b"), R("b", "a")]
    with pytest.raises(CycleError):
        topo_sort(entities, relations)


def test_no_relations():
    entities = [E("z"), E("a"), E("m")]
    result = sorted(e["name"] for e in topo_sort(entities, []))
    assert result == ["a", "m", "z"]
