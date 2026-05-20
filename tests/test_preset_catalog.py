import textwrap

import pytest

from preset_catalog import PRESETS, _load_presets, _merge_global_catalog, _parse_global_seed, is_preset


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
    """YAML catalog must round-trip the original 5 hardcoded domains + Growth-2D/Growth-9 additions."""
    assert set(PRESETS.keys()) == {
        "고객관리", "주문관리", "재고관리", "인사관리", "재무관리",
        "게시판", "권한관리", "공통코드",
        "결재", "알림", "파일관리",
    }
    # Growth-2D: 게시판 new domain (community/CMS pattern)
    assert PRESETS["게시판"] == {"board", "post", "comment", "attachment"}
    # Growth-2B: stock_movement added to 재고관리 (입출고 audit pattern)
    assert PRESETS["재고관리"] == {"product", "sku", "warehouse", "stock", "stock_movement"}
    # Growth-1: customer_category added to 고객관리 (catalog deepening)
    assert PRESETS["고객관리"] == {"customer", "customer_category", "address", "contact_log"}
    # Growth-2A: order_status_history added to 주문관리 (audit pattern)
    assert PRESETS["주문관리"] == {"sales_order", "order_item", "payment", "order_status_history"}
    # Growth-2C: attendance added to 인사관리 (daily transaction pattern)
    assert PRESETS["인사관리"] == {"employee", "department", "position", "attendance"}
    # Growth-9 + Growth-21a-1: 권한관리 RBAC foundation + OAuth2 link entities
    # (oauth_account/refresh_token added to support standalone shell OAuth2 + JWT flow)
    assert PRESETS["권한관리"] == {
        "app_user", "role", "permission", "user_role", "role_permission", "login_audit",
        "oauth_account", "refresh_token",
    }
    # Growth-10: 공통코드 new domain (lookup table — every enum varchar should FK here)
    assert PRESETS["공통코드"] == {"code_group", "code", "code_history"}
    # Growth-11: 결재 new domain (한국 SI 필수 — workflow + line + audit)
    assert PRESETS["결재"] == {
        "approval_template", "approval_request", "approval_line", "approval_history",
    }
    # Growth-12: 알림 new domain (event → user 통지 단일 경로)
    assert PRESETS["알림"] == {
        "notification_template", "notification", "notification_subscription", "notification_log",
    }
    # Growth-13: 파일관리 new domain (binary asset + ACL + access log)
    assert PRESETS["파일관리"] == {
        "file_folder", "file", "file_acl", "file_access_log",
    }


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


# --- Global catalog merge tests --------------------------------------------

GLOBAL_SEED = textwrap.dedent("""\
    ---
    preset: 고객관리
    version: 2
    ---

    ### vip_customer
    ```yaml
    type: entity
    name: vip_customer
    columns:
      - { name: id, type: bigserial, pk: true }
    ```

    ### loyalty_program
    ```yaml
    type: entity
    name: loyalty_program
    columns: []
    ```
""")


def test_parse_global_seed_extracts_entity_names(tmp_path):
    p = tmp_path / "고객관리.seed.md"
    p.write_text(GLOBAL_SEED, encoding="utf-8")
    assert _parse_global_seed(p) == {"vip_customer", "loyalty_program"}


def test_parse_global_seed_missing_file_returns_empty(tmp_path):
    assert _parse_global_seed(tmp_path / "nope.seed.md") == set()


def test_parse_global_seed_skips_non_entity_blocks(tmp_path):
    p = tmp_path / "x.seed.md"
    p.write_text(textwrap.dedent("""\
        ```yaml
        type: concept
        name: ignored
        ```

        ```yaml
        type: entity
        name: kept
        ```
    """), encoding="utf-8")
    assert _parse_global_seed(p) == {"kept"}


def test_merge_global_catalog_augments_existing_domain(tmp_path):
    (tmp_path / "고객관리.seed.md").write_text(GLOBAL_SEED, encoding="utf-8")
    local = {"고객관리": {"customer", "address"}}
    out = _merge_global_catalog(local, tmp_path)
    assert out["고객관리"] == {"customer", "address", "vip_customer", "loyalty_program"}


def test_merge_global_catalog_adds_new_domain(tmp_path):
    (tmp_path / "신규도메인.seed.md").write_text(GLOBAL_SEED, encoding="utf-8")
    local = {"고객관리": {"customer"}}
    out = _merge_global_catalog(local, tmp_path)
    assert "신규도메인" in out
    assert out["고객관리"] == {"customer"}  # untouched


def test_merge_global_catalog_missing_dir_returns_input(tmp_path):
    local = {"고객관리": {"customer"}}
    out = _merge_global_catalog(local, tmp_path / "nope")
    assert out == local


def test_merge_global_catalog_no_local_mutation(tmp_path):
    (tmp_path / "고객관리.seed.md").write_text(GLOBAL_SEED, encoding="utf-8")
    local = {"고객관리": {"customer"}}
    _merge_global_catalog(local, tmp_path)
    assert local == {"고객관리": {"customer"}}, "local input must not be mutated"
