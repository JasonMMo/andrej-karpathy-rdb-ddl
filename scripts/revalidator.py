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


def _v002_fk_targets(blueprint: dict) -> List[Dict]:
    diags = []
    by_name = {e["name"]: e for e in blueprint.get("entities", [])}
    for r in blueprint.get("relations", []):
        target = by_name.get(r.get("to"))
        if target is None:
            diags.append(_diag("V002", "ERROR",
                               f"relation {r.get('from')}->{r.get('to')}: target entity not found",
                               relation=r))
            continue
        target_cols = target.get("columns") or []
        if not any(c.get("pk") for c in target_cols):
            diags.append(_diag("V002", "ERROR",
                               f"relation {r.get('from')}->{r.get('to')}: target has no PK",
                               relation=r))
    return diags


def revalidate(blueprint: dict, dialect: str = "postgres") -> List[Dict]:
    diags = []
    for e in blueprint.get("entities", []):
        diags.extend(_v001_pk_exists(e))
    diags.extend(_v002_fk_targets(blueprint))
    return diags
