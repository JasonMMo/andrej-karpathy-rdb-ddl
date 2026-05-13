from preset_catalog import is_preset


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
