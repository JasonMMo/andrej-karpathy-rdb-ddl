from revalidator import revalidate


def bp(entities=None, relations=None, business_rules=None):
    return {
        "version": 1,
        "entities": entities or [],
        "relations": relations or [],
        "business_rules": business_rules or [],
    }


def test_v001_pk_exists_green():
    e = {"name": "c", "table": "c", "schema": "crm",
         "columns": [{"name": "id", "type": "bigserial", "pk": True}]}
    diags = revalidate(bp(entities=[e]))
    assert not any(d["code"] == "V001" for d in diags)


def test_v001_no_pk_error():
    e = {"name": "c", "table": "c", "schema": "crm",
         "columns": [{"name": "name", "type": "varchar"}]}
    diags = revalidate(bp(entities=[e]))
    v001 = [d for d in diags if d["code"] == "V001"]
    assert len(v001) == 1
    assert v001[0]["severity"] == "ERROR"
    assert "c" in v001[0]["message"]


def _ent(name, cols=None):
    return {"name": name, "table": name, "schema": "crm",
            "columns": cols or [{"name": "id", "type": "bigserial", "pk": True}]}


def test_v002_fk_target_exists_green():
    customer = _ent("customer")
    address = _ent("address", [
        {"name": "id", "type": "bigserial", "pk": True},
        {"name": "customer_id", "type": "bigint"},
    ])
    r = {"from": "address", "to": "customer", "fk": "customer_id"}
    diags = revalidate(bp(entities=[customer, address], relations=[r]))
    assert not any(d["code"] == "V002" for d in diags)


def test_v002_missing_target_error():
    address = _ent("address", [
        {"name": "id", "type": "bigserial", "pk": True},
        {"name": "ghost_id", "type": "bigint"},
    ])
    r = {"from": "address", "to": "ghost", "fk": "ghost_id"}
    diags = revalidate(bp(entities=[address], relations=[r]))
    v002 = [d for d in diags if d["code"] == "V002"]
    assert len(v002) == 1
    assert v002[0]["severity"] == "ERROR"


def test_v002_target_no_pk_error():
    pk_less = {"name": "x", "table": "x", "schema": "s",
               "columns": [{"name": "n", "type": "varchar"}]}
    src = _ent("src", [
        {"name": "id", "type": "bigserial", "pk": True},
        {"name": "x_id", "type": "bigint"},
    ])
    r = {"from": "src", "to": "x", "fk": "x_id"}
    diags = revalidate(bp(entities=[pk_less, src], relations=[r]))
    assert any(d["code"] == "V002" for d in diags)
