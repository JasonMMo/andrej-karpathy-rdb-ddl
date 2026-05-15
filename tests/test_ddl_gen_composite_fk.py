"""복합 FK constraint 생성 테스트."""
from ddl_gen import _fk_columns, _gather_foreign_keys, generate_ddl


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


def test_generate_ddl_composite_fk_emits_multi_column_constraint(tmp_path):
    """Composite FK with two columns renders a comma-joined column list in SQL."""
    # order_item owns (order_id, seq) FK columns; order_hdr is the parent with PK (id).
    # FK column names differ from the parent PK so ownership is unambiguous.
    blueprint = {
        "project": {"name": "t"},
        "entities": [
            {"name": "order_hdr", "schema": "app", "table": "order_hdr",
             "columns": [
                 {"name": "id", "type": "bigint", "pk": True},
                 {"name": "customer_id", "type": "bigint"},
             ]},
            {"name": "order_item", "schema": "app", "table": "order_item",
             "columns": [
                 {"name": "id", "type": "bigint", "pk": True},
                 {"name": "order_id", "type": "bigint"},
                 {"name": "seq", "type": "int"},
                 {"name": "qty", "type": "int"},
             ]},
        ],
        "relations": [{
            "from": "order_hdr", "to": "order_item",
            "fk": {"column": ["order_id", "seq"], "on_delete": "cascade"},
        }],
    }
    generate_ddl(blueprint, tmp_path, dialect="postgres")
    sql = (tmp_path / "migrations" / "V004__create_constraints.sql").read_text(encoding="utf-8")
    assert "FOREIGN KEY (order_id, seq)" in sql
    assert "REFERENCES app.order_hdr(id)" in sql
    assert "ON DELETE CASCADE" in sql
