"""복합 FK constraint 생성 테스트."""
from ddl_gen import _fk_columns, _gather_foreign_keys


def test_fk_columns_single_string():
    assert _fk_columns({"fk": "user_id"}) == ["user_id"]


def test_fk_columns_nested_string():
    assert _fk_columns({"fk": {"column": "user_id"}}) == ["user_id"]


def test_fk_columns_nested_list():
    assert _fk_columns({"fk": {"column": ["a_id", "b_id"]}}) == ["a_id", "b_id"]


def test_fk_columns_missing():
    assert _fk_columns({}) == []


def test_gather_composite_fk_constraint_name_and_columns():
    blueprint = {
        "relations": [{
            "from": "user_role", "to": "user",
            "fk": {"column": ["user_id"], "on_delete": "cascade"},
        }],
    }
    by_name = {
        "user_role": {
            "name": "user_role", "schema": "app", "table": "user_role",
            "columns": [{"name": "user_id", "pk": True}, {"name": "role_id", "pk": True}],
        },
        "user": {
            "name": "user", "schema": "app", "table": "user",
            "columns": [{"name": "user_id", "pk": True}],
        },
    }
    fks = _gather_foreign_keys(blueprint, by_name)
    assert len(fks) == 1
    assert fks[0]["columns"] == ["user_id"]
    assert fks[0]["ref_columns"] == ["user_id"]
    assert fks[0]["name"] == "fk_user_role__user_id"
