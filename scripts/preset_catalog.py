PRESETS = {
    "고객관리": {"customer", "address", "contact_log"},
    "주문관리": {"sales_order", "order_item", "payment"},
    "재고관리": {"product", "sku", "warehouse", "stock"},
    "인사관리": {"employee", "department", "position"},
    "재무관리": {"account", "fiscal_period", "ledger_entry"},
}


def build_domain_index(blueprint: dict) -> dict:
    """blueprint['domains'][i]['entities'][] → {entity_name: [domain_name, ...]}.

    Returns empty dict if blueprint has no top-level `domains`. Use this so
    `is_preset` can resolve domain membership from blueprint-spec.md output."""
    idx: dict = {}
    for d in blueprint.get("domains") or []:
        dn = d.get("name")
        if not dn:
            continue
        for en in d.get("entities") or []:
            idx.setdefault(en, []).append(dn)
    return idx


def _domains(entity: dict, domain_index):
    if domain_index is not None:
        return list(domain_index.get(entity.get("name"), []))
    d = entity.get("domain")
    if d is None:
        return []
    if isinstance(d, str):
        return [d]
    return list(d)


def is_preset(entity: dict, domain_index=None) -> bool:
    if entity.get("preset"):
        return True
    name = entity.get("name")
    for domain in _domains(entity, domain_index):
        if name in PRESETS.get(domain, set()):
            return True
    return False
