import pytest
from dialect import get_dialect


REQUIRED_TYPE_KEYS = [
    "bigserial", "bigint", "integer", "varchar",
    "text", "boolean", "timestamp", "date", "numeric",
]


def test_mysql_registered():
    d = get_dialect("mysql")
    assert d.name == "mysql"
    assert d.template_dir == "mysql"


def test_mysql_type_map_complete():
    d = get_dialect("mysql")
    missing = [k for k in REQUIRED_TYPE_KEYS if k not in d.type_map]
    assert not missing, f"missing type_map keys: {missing}"


def test_mysql_type_map_values():
    d = get_dialect("mysql")
    assert d.type_map["bigserial"] == "BIGINT AUTO_INCREMENT"
    assert d.type_map["bigint"] == "BIGINT"
    assert d.type_map["integer"] == "INT"
    assert d.type_map["boolean"] == "TINYINT(1)"
    assert d.type_map["timestamp"] == "DATETIME"


def test_mysql_schema_strategy_and_ops():
    d = get_dialect("mysql")
    assert d.schema_strategy == "native"
    assert d.idempotent_insert == "INSERT IGNORE"
    assert d.regex_op == "REGEXP"
