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


def test_v003_naming_green():
    e = _ent("customer", [{"name": "id", "type": "bigserial", "pk": True},
                          {"name": "email", "type": "varchar"}])
    diags = revalidate(bp(entities=[e]))
    assert not any(d["code"] == "V003" for d in diags)


def test_v003_camel_case_error():
    e = _ent("Customer", [{"name": "id", "type": "bigserial", "pk": True}])
    diags = revalidate(bp(entities=[e]))
    assert any(d["code"] == "V003" for d in diags)


def test_v003_reserved_word_error():
    e = _ent("user", [{"name": "id", "type": "bigserial", "pk": True}])
    diags = revalidate(bp(entities=[e]))
    assert any(d["code"] == "V003" for d in diags)


def test_v003_too_long_error():
    e = _ent("a" * 64, [{"name": "id", "type": "bigserial", "pk": True}])
    diags = revalidate(bp(entities=[e]))
    assert any(d["code"] == "V003" for d in diags)


def test_v004_schema_present_green():
    e = _ent("customer")
    e["schema"] = "crm"
    diags = revalidate(bp(entities=[e]))
    assert not any(d["code"] == "V004" for d in diags)


def test_v004_schema_missing_error():
    e = _ent("customer")
    e.pop("schema", None)
    diags = revalidate(bp(entities=[e]))
    assert any(d["code"] == "V004" for d in diags)


def test_v004_cross_schema_fk_undeclared():
    a = _ent("a"); a["schema"] = "s1"
    b = _ent("b", [{"name": "id", "type": "bigserial", "pk": True},
                   {"name": "a_id", "type": "bigint"}])
    b["schema"] = "s2"
    r = {"from": "b", "to": "a", "fk": "a_id"}
    diags = revalidate(bp(entities=[a, b], relations=[r]))
    assert any(d["code"] == "V004" for d in diags)


def test_v004_cross_schema_fk_declared():
    a = _ent("a"); a["schema"] = "s1"
    b = _ent("b", [{"name": "id", "type": "bigserial", "pk": True},
                   {"name": "a_id", "type": "bigint"}])
    b["schema"] = "s2"
    r = {"from": "b", "to": "a", "fk": "a_id", "cross_schema": True}
    diags = revalidate(bp(entities=[a, b], relations=[r]))
    assert not any(d["code"] == "V004" for d in diags)


def test_v005_simple_check_postgres_pass():
    br = {"name": "chk_age", "enforced_by": "age >= 0"}
    diags = revalidate(bp(business_rules=[br]), dialect="postgres")
    assert not any(d["code"] == "V005" for d in diags)


def test_v005_regex_postgres_pass():
    br = {"name": "chk_email", "enforced_by": "email ~ '^[^@]+@[^@]+$'"}
    diags = revalidate(bp(business_rules=[br]), dialect="postgres")
    assert not any(d["code"] == "V005" for d in diags)


def test_v005_regex_hsqldb_warns():
    br = {"name": "chk_email", "enforced_by": "email ~ '^[^@]+@[^@]+$'"}
    diags = revalidate(bp(business_rules=[br]), dialect="hsqldb")
    v005 = [d for d in diags if d["code"] == "V005"]
    assert len(v005) == 1
    assert v005[0]["severity"] == "WARN"


def test_v005_empty_expression_warns():
    br = {"name": "chk_x", "enforced_by": ""}
    diags = revalidate(bp(business_rules=[br]), dialect="postgres")
    assert any(d["code"] == "V005" for d in diags)
