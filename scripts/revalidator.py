import re
from typing import List, Dict

from dialect import get_dialect


def _diag(code: str, severity: str, message: str, **kw) -> Dict:
    d = {"code": code, "severity": severity, "message": message}
    d.update(kw)
    return d


def _v001_pk_exists(entity: dict) -> List[Dict]:
    cols = entity.get("columns") or []
    if not any(c.get("pk") for c in cols):
        return [_diag("V001", "ERROR",
                      f"entity '{entity.get('name')}' has no PK column",
                      entity=entity.get("name"))]
    return []


def revalidate(blueprint: dict, dialect: str = "postgres") -> List[Dict]:
    diags = []
    for e in blueprint.get("entities", []):
        diags.extend(_v001_pk_exists(e))
    return diags
