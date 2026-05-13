import pathlib
from ddl_gen import generate_ddl


def make_blueprint():
    return {
        "version": 1,
        "entities": [
            {"name": "customer", "table": "customer", "schema": "crm",
             "columns": [
                 {"name": "id", "type": "bigserial", "pk": True, "null": False},
                 {"name": "email", "type": "varchar(255)", "null": False},
             ],
             "indexes": [{"name": "ix_customer_email", "columns": ["email"], "unique": True}]},
            {"name": "address", "table": "address", "schema": "crm",
             "columns": [
                 {"name": "id", "type": "bigserial", "pk": True, "null": False},
                 {"name": "customer_id", "type": "bigint", "null": False},
             ]},
        ],
        "relations": [
            {"from": "address", "to": "customer", "fk": "customer_id", "on_delete": "cascade"},
        ],
        "business_rules": [],
    }


def test_v001_creates_schema(tmp_path):
    generate_ddl(make_blueprint(), tmp_path, dialect="postgres")
    v001 = (tmp_path / "migrations" / "V001__create_schema.sql").read_text(encoding="utf-8")
    assert "CREATE SCHEMA IF NOT EXISTS crm;" in v001


def test_v002_creates_tables_in_toposort(tmp_path):
    generate_ddl(make_blueprint(), tmp_path, dialect="postgres")
    v002 = (tmp_path / "migrations" / "V002__create_tables.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS crm.customer" in v002
    assert "CREATE TABLE IF NOT EXISTS crm.address" in v002
    assert v002.index("crm.customer") < v002.index("crm.address")


def test_v002_uses_bigserial_for_postgres(tmp_path):
    generate_ddl(make_blueprint(), tmp_path, dialect="postgres")
    v002 = (tmp_path / "migrations" / "V002__create_tables.sql").read_text(encoding="utf-8")
    assert "BIGSERIAL" in v002


def test_v003_creates_unique_index(tmp_path):
    generate_ddl(make_blueprint(), tmp_path, dialect="postgres")
    v003 = (tmp_path / "migrations" / "V003__create_indexes.sql").read_text(encoding="utf-8")
    assert "CREATE UNIQUE INDEX IF NOT EXISTS ix_customer_email" in v003
    assert "ON crm.customer (email)" in v003


def test_v004_creates_fk(tmp_path):
    generate_ddl(make_blueprint(), tmp_path, dialect="postgres")
    v004 = (tmp_path / "migrations" / "V004__create_constraints.sql").read_text(encoding="utf-8")
    assert "ALTER TABLE crm.address" in v004
    assert "REFERENCES crm.customer(id)" in v004
    assert "ON DELETE CASCADE" in v004


def test_v004_creates_check(tmp_path):
    bp = make_blueprint()
    bp["business_rules"] = [{
        "name": "chk_email_format",
        "applies_to": "customer",
        "enforced_by": "email LIKE '%@%'",
    }]
    generate_ddl(bp, tmp_path, dialect="postgres")
    v004 = (tmp_path / "migrations" / "V004__create_constraints.sql").read_text(encoding="utf-8")
    assert "chk_email_format" in v004
    assert "CHECK (email LIKE '%@%')" in v004
