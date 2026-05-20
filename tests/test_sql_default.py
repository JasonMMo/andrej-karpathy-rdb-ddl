"""Tests for the _sql_default Jinja filter (cross-dialect default value safety).

Postgres rejects unquoted identifiers in DEFAULT clauses
(e.g., `DEFAULT pending` -> syntax error; must be `DEFAULT 'pending'`).
HSQLDB and MySQL accept both but emit warnings or coerce.

The filter must:
- quote bare string literals  ('pending' -> "'pending'")
- preserve SQL function calls  (NOW() -> NOW())
- preserve SQL keywords        (CURRENT_TIMESTAMP, NULL, TRUE/FALSE)
- emit TRUE/FALSE for Python bools
- emit numeric literals raw    (0, 1.5)
- escape single quotes in strings (O'Brien -> 'O''Brien')
"""
import pathlib
import pytest
from ddl_gen import _sql_default, generate_ddl


def test_string_literal_is_quoted():
    assert _sql_default("pending") == "'pending'"


def test_string_with_apostrophe_is_escaped():
    assert _sql_default("O'Brien") == "'O''Brien'"


def test_function_call_passes_through():
    assert _sql_default("NOW()") == "NOW()"
    assert _sql_default("gen_random_uuid()") == "gen_random_uuid()"


def test_sql_keywords_pass_through_uppercased():
    assert _sql_default("CURRENT_TIMESTAMP") == "CURRENT_TIMESTAMP"
    assert _sql_default("current_timestamp") == "CURRENT_TIMESTAMP"
    assert _sql_default("NULL") == "NULL"


def test_python_bool_becomes_sql_bool():
    assert _sql_default(True) == "TRUE"
    assert _sql_default(False) == "FALSE"


def test_python_string_true_false_pass_through():
    # YAML loads `True`/`False` as Python booleans, but a quoted "True"
    # in YAML stays a string — should still resolve to SQL TRUE keyword.
    assert _sql_default("True") == "TRUE"
    assert _sql_default("false") == "FALSE"


def test_numeric_passes_through():
    assert _sql_default(0) == "0"
    assert _sql_default(42) == "42"
    assert _sql_default(1.5) == "1.5"


def test_none_and_empty_return_empty_string():
    assert _sql_default(None) == ""
    assert _sql_default("") == ""
    assert _sql_default("   ") == ""


def _bp_with_string_default():
    return {
        "version": 1,
        "entities": [{
            "name": "task", "table": "task", "schema": "wf",
            "columns": [
                {"name": "id", "type": "bigserial", "pk": True, "nullable": False},
                {"name": "status", "type": "varchar(32)", "nullable": False,
                 "default": "pending"},
                {"name": "active", "type": "boolean", "nullable": False,
                 "default": True},
                {"name": "created_at", "type": "timestamp", "nullable": False,
                 "default": "CURRENT_TIMESTAMP"},
            ],
        }],
        "relations": [],
        "business_rules": [],
    }


@pytest.mark.parametrize("dialect", ["postgres", "hsqldb", "mysql"])
def test_tables_sql_quotes_string_defaults_in_all_dialects(tmp_path, dialect):
    generate_ddl(_bp_with_string_default(), tmp_path, dialect=dialect)
    v002 = (tmp_path / "migrations" / "V002__create_tables.sql").read_text(encoding="utf-8")
    assert "DEFAULT 'pending'" in v002, f"{dialect}: string default must be quoted"
    assert "DEFAULT pending" not in v002, f"{dialect}: bare identifier leaks (postgres-incompatible)"
    assert "DEFAULT TRUE" in v002, f"{dialect}: bool default must be SQL TRUE keyword"
    assert "DEFAULT CURRENT_TIMESTAMP" in v002, f"{dialect}: keyword default must pass through raw"
