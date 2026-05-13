PRESETS = {
    "고객관리": {"customer", "address", "contact_log"},
    "주문관리": {"sales_order", "order_item", "payment"},
    "재고관리": {"product", "sku", "warehouse", "stock"},
    "인사관리": {"employee", "department", "position"},
    "재무관리": {"account", "fiscal_period", "ledger_entry"},
}


def _domains(entity: dict):
    d = entity.get("domain")
    if d is None:
        return []
    if isinstance(d, str):
        return [d]
    return list(d)


def is_preset(entity: dict) -> bool:
    if entity.get("preset"):
        return True
    name = entity.get("name")
    for domain in _domains(entity):
        if name in PRESETS.get(domain, set()):
            return True
    return False
