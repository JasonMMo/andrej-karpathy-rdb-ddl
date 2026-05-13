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
