"""Regression tests for blueprint-spec.md alignment (v0.1.1)."""
import pathlib

from ddl_gen import _gather_foreign_keys, _fk_on_delete
from preset_catalog import build_domain_index, is_preset
from revalidator import revalidate
from seed_gen import generate_seed


def _bp_spec():
    """Minimal blueprint-spec.md-style payload."""
    return {
        "version": 1,
        "project": "ex",
        "domains": [
            {"name": "고객관리", "description": "", "entities": ["customer", "address"]},
        ],
        "entities": [
            {"name": "customer", "table": "customer", "schema": "crm",
             "columns": [
                 {"name": "id", "type": "bigserial", "pk": True, "nullable": False},
                 {"name": "email", "type": "varchar(255)", "nullable": False},
             ]},
            {"name": "address", "table": "address", "schema": "crm",
             "columns": [
                 {"name": "id", "type": "bigserial", "pk": True, "nullable": False},
                 {"name": "customer_id", "type": "bigint", "nullable": False},
             ]},
        ],
        "relations": [
            {"from": "customer", "to": "address", "cardinality": "1:N",
             "fk": {"column": "customer_id", "on_delete": "cascade"},
             "concept_name": "customer-has-many-addresses"},
        ],
        "business_rules": [],
    }


def test_domain_index_built_from_top_level_domains():
    idx = build_domain_index(_bp_spec())
    assert idx == {"customer": ["고객관리"], "address": ["고객관리"]}


def test_is_preset_via_domain_index_without_entity_domain_field():
    e = {"name": "customer"}
    assert is_preset(e, {"customer": ["고객관리"]}) is True
    assert is_preset(e, {"customer": ["기타"]}) is False
    assert is_preset(e) is False


def test_fk_on_delete_defaults_to_restrict():
    assert _fk_on_delete({"fk": {"column": "x"}}) == "RESTRICT"
    assert _fk_on_delete({}) == "RESTRICT"
    assert _fk_on_delete({"fk": {"column": "x", "on_delete": "set_null"}}) == "SET NULL"


def test_gather_fks_locates_owner_when_fk_on_to_entity():
    bp = _bp_spec()
    by_name = {e["name"]: e for e in bp["entities"]}
    fks = _gather_foreign_keys(bp, by_name)
    assert len(fks) == 1
    fk = fks[0]
    assert fk["name"] == "fk_address__customer_id"
    assert fk["src_table"] == "address"
    assert fk["columns"] == ["customer_id"]
    assert fk["ref_table"] == "customer"
    assert fk["ref_columns"] == ["id"]
    assert fk["on_delete"] == "CASCADE"


def test_v002_errors_when_fk_column_missing_from_both_sides():
    bp = _bp_spec()
    # Strip the FK column from address — it should fail V002 even though target
    # has a PK, because no entity owns the FK column.
    bp["entities"][1]["columns"] = [
        {"name": "id", "type": "bigserial", "pk": True, "nullable": False},
    ]
    diags = revalidate(bp)
    v002 = [d for d in diags if d["code"] == "V002"]
    assert len(v002) == 1
    assert "customer_id" in v002[0]["message"]


def test_seed_generated_from_domain_index(tmp_path):
    bp = _bp_spec()
    idx = build_domain_index(bp)
    generate_seed(bp["entities"], tmp_path, dialect="postgres", domain_index=idx)
    assert (tmp_path / "seed" / "01_customer_sample.sql").exists()
    assert (tmp_path / "seed" / "01_address_sample.sql").exists()


def test_legacy_null_key_string_form_emits_not_null(tmp_path):
    """Legacy column dict with string key 'null': False must produce NOT NULL DDL."""
    from ddl_gen import generate_ddl
    entities = [{
        "name": "customer", "schema": "public", "table": "customer",
        "columns": [
            {"name": "id", "type": "bigserial", "pk": True, "null": False},
            {"name": "email", "type": "varchar(255)", "null": False, "unique": True},
        ],
    }]
    generate_ddl({"entities": entities, "relations": [], "business_rules": []}, tmp_path, dialect="postgres")
    sql = (tmp_path / "migrations" / "V002__create_tables.sql").read_text(encoding="utf-8")
    assert "id BIGSERIAL PRIMARY KEY NOT NULL" in sql
    assert "email VARCHAR(255) NOT NULL" in sql


def test_legacy_null_key_none_form_emits_not_null(tmp_path):
    """Column dict with Python None key (from YAML `null:` literal) must still produce NOT NULL."""
    from ddl_gen import generate_ddl
    entities = [{
        "name": "customer", "schema": "public", "table": "customer",
        "columns": [
            {"name": "id", "type": "bigserial", "pk": True, None: False},
            {"name": "email", "type": "varchar(255)", None: False},
        ],
    }]
    generate_ddl({"entities": entities, "relations": [], "business_rules": []}, tmp_path, dialect="postgres")
    sql = (tmp_path / "migrations" / "V002__create_tables.sql").read_text(encoding="utf-8")
    assert "email VARCHAR(255) NOT NULL" in sql
