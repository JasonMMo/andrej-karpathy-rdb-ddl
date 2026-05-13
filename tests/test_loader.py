import pytest
import pathlib
from loader import load_blueprint, BlueprintError


def write(tmp_path, content):
    p = tmp_path / "_blueprint.yaml"
    p.write_text(content, encoding="utf-8")
    return p


def test_load_valid_blueprint(tmp_path):
    p = write(tmp_path, """
version: 1
project: 테스트
entities: []
relations: []
business_rules: []
validation:
  passed: true
""")
    bp = load_blueprint(p)
    assert bp["version"] == 1
    assert bp["project"] == "테스트"


def test_reject_missing_version(tmp_path):
    p = write(tmp_path, """
project: x
validation: {passed: true}
""")
    with pytest.raises(BlueprintError, match="version"):
        load_blueprint(p)


def test_reject_wrong_version(tmp_path):
    p = write(tmp_path, """
version: 99
project: x
validation: {passed: true}
""")
    with pytest.raises(BlueprintError, match="version"):
        load_blueprint(p)


def test_reject_failed_validation(tmp_path):
    p = write(tmp_path, """
version: 1
project: x
validation: {passed: false}
""")
    with pytest.raises(BlueprintError, match="Stage 1 validation failed"):
        load_blueprint(p)


def test_reject_missing_file(tmp_path):
    with pytest.raises(BlueprintError, match="not found"):
        load_blueprint(tmp_path / "missing.yaml")
