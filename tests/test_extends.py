"""Tests for loader.py extends resolution (Phase 2.2, blueprint v0.2+)."""
import pathlib
import textwrap

import pytest

from loader import BlueprintError, _find_catalog_entity, _resolve_extends, load_blueprint

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BP_HEADER = textwrap.dedent("""\
    version: 1
    project: test
    validation: {passed: true}
    relations: []
    business_rules: []
""")

_BASE_SEED = textwrap.dedent("""\
    ---
    preset: 고객관리
    version: 1
    ---

    ### base_customer
    ```yaml
    type: entity
    name: base_customer
    table: base_customer
    columns:
      - {name: id, type: bigserial, pk: true, nullable: false}
      - {name: email, type: varchar(255), nullable: false}
      - {name: created_at, type: timestamptz, nullable: false}
    indexes:
      - {name: ix_base_email, columns: [email], unique: true}
    ```
""")


def _write_bp(tmp_path: pathlib.Path, entities_yaml: str) -> pathlib.Path:
    p = tmp_path / "_blueprint.yaml"
    p.write_text(_BP_HEADER + f"entities:\n{entities_yaml}", encoding="utf-8")
    return p


def _make_catalog(tmp_path: pathlib.Path, seed_content: str = _BASE_SEED) -> pathlib.Path:
    cat = tmp_path / "catalog"
    cat.mkdir()
    (cat / "고객관리.seed.md").write_text(seed_content, encoding="utf-8")
    return cat


# ---------------------------------------------------------------------------
# _find_catalog_entity
# ---------------------------------------------------------------------------


def test_find_entity_present(tmp_path):
    cat = _make_catalog(tmp_path)
    result = _find_catalog_entity("base_customer", cat)
    assert result is not None
    assert result["name"] == "base_customer"
    assert any(c["name"] == "email" for c in result["columns"])


def test_find_entity_absent_returns_none(tmp_path):
    cat = _make_catalog(tmp_path)
    assert _find_catalog_entity("no_such_entity", cat) is None


def test_find_entity_missing_catalog_dir(tmp_path):
    assert _find_catalog_entity("x", tmp_path / "nonexistent") is None


# ---------------------------------------------------------------------------
# _resolve_extends
# ---------------------------------------------------------------------------


def test_resolve_no_extends_passthrough():
    entity = {"name": "plain", "table": "plain", "columns": [{"name": "id"}]}
    result = _resolve_extends(entity, pathlib.Path("/nonexistent"))
    assert result == entity


def test_resolve_extends_merges_base_columns(tmp_path):
    cat = _make_catalog(tmp_path)
    entity = {"name": "child", "table": "child", "extends": "base_customer", "columns": []}
    result = _resolve_extends(entity, cat)
    assert "extends" not in result
    col_names = [c["name"] for c in result["columns"]]
    assert "id" in col_names
    assert "email" in col_names
    assert "created_at" in col_names


def test_resolve_extends_merges_base_indexes(tmp_path):
    cat = _make_catalog(tmp_path)
    entity = {"name": "child", "table": "child", "extends": "base_customer", "indexes": []}
    result = _resolve_extends(entity, cat)
    idx_names = [i["name"] for i in result.get("indexes", [])]
    assert "ix_base_email" in idx_names


def test_resolve_extends_current_overrides_base_column(tmp_path):
    cat = _make_catalog(tmp_path)
    override_col = {"name": "email", "type": "varchar(320)", "nullable": False}
    entity = {
        "name": "child",
        "table": "child",
        "extends": "base_customer",
        "columns": [override_col],
    }
    result = _resolve_extends(entity, cat)
    email_col = next(c for c in result["columns"] if c["name"] == "email")
    assert email_col["type"] == "varchar(320)", "current entity column must override base"


def test_resolve_extends_current_adds_new_column(tmp_path):
    cat = _make_catalog(tmp_path)
    new_col = {"name": "phone", "type": "varchar(30)", "nullable": True}
    entity = {
        "name": "child",
        "table": "child",
        "extends": "base_customer",
        "columns": [new_col],
    }
    result = _resolve_extends(entity, cat)
    col_names = [c["name"] for c in result["columns"]]
    assert "phone" in col_names
    assert "id" in col_names  # base column still present


def test_resolve_extends_missing_entity_raises(tmp_path):
    cat = _make_catalog(tmp_path)
    entity = {"name": "child", "extends": "ghost_entity"}
    with pytest.raises(BlueprintError, match="ghost_entity.*not found"):
        _resolve_extends(entity, cat)


def test_resolve_extends_missing_catalog_dir_raises(tmp_path):
    entity = {"name": "child", "extends": "base_customer"}
    with pytest.raises(BlueprintError, match="not found"):
        _resolve_extends(entity, tmp_path / "nonexistent")


# ---------------------------------------------------------------------------
# load_blueprint — extends integration
# ---------------------------------------------------------------------------


def test_load_blueprint_resolves_extends(tmp_path):
    cat = _make_catalog(tmp_path)
    p = _write_bp(tmp_path, textwrap.dedent("""\
        - name: vip_customer
          table: vip_customer
          extends: base_customer
          columns: []
    """))
    bp = load_blueprint(p, catalog_dir=cat)
    entity = bp["entities"][0]
    assert "extends" not in entity
    col_names = [c["name"] for c in entity["columns"]]
    assert "id" in col_names
    assert "email" in col_names


def test_load_blueprint_no_extends_unaffected(tmp_path):
    cat = _make_catalog(tmp_path)
    p = _write_bp(tmp_path, textwrap.dedent("""\
        - name: plain
          table: plain
          columns:
            - {name: id, type: bigserial, pk: true}
    """))
    bp = load_blueprint(p, catalog_dir=cat)
    entity = bp["entities"][0]
    assert entity["name"] == "plain"
    assert len(entity["columns"]) == 1


def test_load_blueprint_missing_extends_entity_raises(tmp_path):
    cat = _make_catalog(tmp_path)
    p = _write_bp(tmp_path, textwrap.dedent("""\
        - name: bad
          table: bad
          extends: does_not_exist
    """))
    with pytest.raises(BlueprintError, match="does_not_exist.*not found"):
        load_blueprint(p, catalog_dir=cat)


