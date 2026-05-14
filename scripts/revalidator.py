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


_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
RESERVED = frozenset({
    "user", "order", "select", "table", "from", "where", "group", "join",
    "index", "primary", "key", "foreign", "check", "constraint", "default",
    "null", "true", "false", "and", "or", "not", "in", "is", "as", "by",
})


def _v003_naming(entity: dict) -> List[Dict]:
    diags = []
    name = entity.get("name", "")
    if not _NAME_RE.match(name):
        diags.append(_diag("V003", "ERROR",
                           f"entity name '{name}' must be snake_case",
                           entity=name))
    if name.lower() in RESERVED:
        diags.append(_diag("V003", "ERROR",
                           f"entity name '{name}' is a SQL reserved word",
                           entity=name))
    if len(name) > 63:
        diags.append(_diag("V003", "ERROR",
                           f"entity name '{name}' exceeds 63 chars",
                           entity=name))
    for col in entity.get("columns") or []:
        cn = col.get("name", "")
        if not _NAME_RE.match(cn):
            diags.append(_diag("V003", "ERROR",
                               f"column '{name}.{cn}' must be snake_case",
                               entity=name, column=cn))
        if len(cn) > 63:
            diags.append(_diag("V003", "ERROR",
                               f"column '{name}.{cn}' exceeds 63 chars",
                               entity=name, column=cn))
    return diags


def _fk_column(relation: dict):
    """Accept both nested `fk.{column}` (blueprint-spec) and legacy flat `fk: <str>`."""
    fk = relation.get("fk")
    if isinstance(fk, dict):
        return fk.get("column")
    return fk


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
            continue
        fk_col = _fk_column(r)
        if fk_col:
            src = by_name.get(r.get("from"))
            src_cols = (src.get("columns") if src else None) or []
            tgt_cols = target.get("columns") or []
            on_src = any(c.get("name") == fk_col for c in src_cols)
            on_tgt = any(c.get("name") == fk_col for c in tgt_cols)
            # Accept either convention: blueprint-spec (fk on `to`, the N-side)
            # or legacy (fk on `from`, the N-side).
            if not (on_src or on_tgt):
                diags.append(_diag("V002", "ERROR",
                                   f"relation {r.get('from')}->{r.get('to')}: fk column "
                                   f"'{fk_col}' not found on either side",
                                   relation=r))
    return diags


def _v004_schema(blueprint: dict) -> List[Dict]:
    diags = []
    by_name = {e["name"]: e for e in blueprint.get("entities", [])}
    for e in blueprint.get("entities", []):
        if not e.get("schema"):
            diags.append(_diag("V004", "ERROR",
                               f"entity '{e.get('name')}' missing schema",
                               entity=e.get("name")))
    for r in blueprint.get("relations", []):
        src = by_name.get(r.get("from"))
        dst = by_name.get(r.get("to"))
        if not src or not dst:
            continue
        if src.get("schema") and dst.get("schema") and src["schema"] != dst["schema"]:
            if not r.get("cross_schema"):
                diags.append(_diag("V004", "ERROR",
                                   f"cross-schema FK {r['from']}->{r['to']} not declared "
                                   "(set relation.cross_schema: true)",
                                   relation=r))
    return diags


def _v005_constraints(blueprint: dict, dialect_name: str) -> List[Dict]:
    d = get_dialect(dialect_name)
    diags = []
    for br in blueprint.get("business_rules") or []:
        rid = br.get("name") or br.get("id")
        raw_expr = br.get("enforced_by")
        # blueprint-spec puts enforced_by as a list of constraint/index names.
        # Legacy puts a SQL expression as a string. Skip lint for list form.
        if isinstance(raw_expr, list):
            continue
        expr = (raw_expr or "").strip()
        if not expr:
            diags.append(_diag("V005", "WARN",
                               f"business rule '{rid}' has empty enforced_by",
                               rule=rid))
            continue
        if "~" in expr and d.regex_op is None:
            diags.append(_diag("V005", "WARN",
                               f"business rule '{rid}' uses regex operator "
                               f"not supported by dialect '{dialect_name}'",
                               rule=rid))
    return diags


def revalidate(blueprint: dict, dialect: str = "postgres") -> List[Dict]:
    diags = []
    for e in blueprint.get("entities", []):
        diags.extend(_v001_pk_exists(e))
        diags.extend(_v003_naming(e))
    diags.extend(_v002_fk_targets(blueprint))
    diags.extend(_v004_schema(blueprint))
    diags.extend(_v005_constraints(blueprint, dialect))
    return diags
