import pytest

from preset_catalog import PRESETS, _load_presets, is_preset


def test_preset_marker_wins():
    e = {"name": "anything", "preset": "고객관리"}
    assert is_preset(e) is True


def test_catalog_match_by_domain_and_name():
    e = {"name": "customer", "domain": ["고객관리"]}
    assert is_preset(e) is True


def test_catalog_match_string_domain():
    e = {"name": "sales_order", "domain": "주문관리"}
    assert is_preset(e) is True


def test_non_preset():
    e = {"name": "random_user_table", "domain": ["기타"]}
    assert is_preset(e) is False


def test_unknown_entity_in_known_domain():
    e = {"name": "totally_made_up", "domain": ["고객관리"]}
    assert is_preset(e) is False


def test_yaml_loaded_all_5_domains():
    """YAML catalog must round-trip the original 5 hardcoded domains."""
    assert set(PRESETS.keys()) == {"고객관리", "주문관리", "재고관리", "인사관리", "재무관리"}
    assert PRESETS["재고관리"] == {"product", "sku", "warehouse", "stock"}


def test_loader_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="preset catalog not found"):
        _load_presets(tmp_path / "nope.yaml")


def test_loader_wrong_version(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("version: 99\ndomains: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported catalog version"):
        _load_presets(p)


def test_loader_bad_top_level(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="top-level must be a mapping"):
        _load_presets(p)


def test_loader_bad_domains_type(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("version: 1\ndomains: not-a-mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="`domains` must be a mapping"):
        _load_presets(p)


def test_loader_bad_entity_list_type(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("version: 1\ndomains:\n  foo: {a: 1}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="entities must be a list"):
        _load_presets(p)


def test_loader_empty_domain_allowed(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("version: 1\ndomains:\n  empty:\n", encoding="utf-8")
    out = _load_presets(p)
    assert out == {"empty": set()}
