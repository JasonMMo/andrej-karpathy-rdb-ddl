import pathlib
import sys
import subprocess

import pytest
from ddl_gen import generate_ddl


FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "golden_blueprint.yaml"
SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "ddl_compile.py"


def make_blueprint():
    return {
        "version": 1,
        "entities": [{
            "name": "customer", "table": "customer", "schema": "crm",
            "columns": [
                {"name": "id", "type": "bigserial", "pk": True, "nullable": False},
                {"name": "email", "type": "varchar(255)", "nullable": False},
            ],
            "indexes": [{"name": "ix_email", "columns": ["email"], "unique": True}],
        }],
        "relations": [],
        "business_rules": [],
    }


def test_mysql_uses_auto_increment(tmp_path):
    generate_ddl(make_blueprint(), tmp_path, dialect="mysql")
    v002 = (tmp_path / "migrations" / "V002__create_tables.sql").read_text(encoding="utf-8")
    assert "BIGINT AUTO_INCREMENT" in v002
    assert "BIGSERIAL" not in v002


def test_mysql_creates_schema_natively(tmp_path):
    generate_ddl(make_blueprint(), tmp_path, dialect="mysql")
    v001 = (tmp_path / "migrations" / "V001__create_schema.sql").read_text(encoding="utf-8")
    assert "CREATE SCHEMA IF NOT EXISTS `crm`" in v001
    assert "utf8mb4" in v001


def test_mysql_uses_backticks_in_tables(tmp_path):
    generate_ddl(make_blueprint(), tmp_path, dialect="mysql")
    v002 = (tmp_path / "migrations" / "V002__create_tables.sql").read_text(encoding="utf-8")
    assert "`crm`.`customer`" in v002
    assert "ENGINE=InnoDB" in v002


def test_mysql_golden_full_render(tmp_path):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURE), "--out", str(tmp_path), "--dialect", "mysql"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    for f in [
        "migrations/V001__create_schema.sql",
        "migrations/V002__create_tables.sql",
        "migrations/V003__create_indexes.sql",
        "migrations/V004__create_constraints.sql",
        "ddl-report.md",
    ]:
        assert (tmp_path / f).exists(), f"missing {f}"
    v002 = (tmp_path / "migrations" / "V002__create_tables.sql").read_text(encoding="utf-8")
    assert "BIGINT AUTO_INCREMENT" in v002
    assert "DATETIME" in v002
    v004 = (tmp_path / "migrations" / "V004__create_constraints.sql").read_text(encoding="utf-8")
    assert "fk_address__customer_id" in v004


@pytest.mark.skip(reason="No embedded MySQL available — in-DB validation deferred to integration env")
def test_mysql_inDB_validation():
    pass
