import pathlib
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from dialect import get_dialect
from toposort import topo_sort


TEMPLATE_ROOT = pathlib.Path(__file__).resolve().parent.parent / ".claude" / "skills" / "karpathy-rdb-ddl" / "templates"


_SQL_RAW_DEFAULTS = {
    "CURRENT_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIME",
    "NOW()", "NULL", "TRUE", "FALSE",
}


def _sql_default(value):
    """Render a YAML-declared default safely across dialects.

    Numbers/bools/SQL function-calls render raw; bare strings are
    single-quoted (Postgres rejects unquoted identifiers in DEFAULT,
    e.g. `DEFAULT pending` — must be `DEFAULT 'pending'`).
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value).strip()
    if not s:
        return ""
    if s.endswith(")"):
        return s
    if s.upper() in _SQL_RAW_DEFAULTS:
        return s.upper()
    return "'" + s.replace("'", "''") + "'"


def _env(dialect_dir: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_ROOT / dialect_dir)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["sql_default"] = _sql_default
    return env


def _normalize_columns(entity: dict, dialect) -> list:
    cols = []
    for c in entity.get("columns") or []:
        c2 = dict(c)
        # Legacy / mis-quoted YAML may surface `null` as Python None key or string "null"
        if None in c2:
            c2["nullable"] = c2.pop(None)
        if "null" in c2 and "nullable" not in c2:
            c2["nullable"] = c2.pop("null")
        raw_type = c.get("type", "").strip()
        base = raw_type.split("(")[0].lower()
        mapped = dialect.type_map.get(base, raw_type.upper())
        if "(" in raw_type and base in {"varchar", "numeric"}:
            mapped = mapped + raw_type[raw_type.index("("):]
        c2["sql_type"] = mapped
        # Ensure template attributes are defined to avoid StrictUndefined errors
        c2.setdefault("pk", False)
        c2.setdefault("nullable", True)
        c2.setdefault("default", None)
        cols.append(c2)
    return cols


def _gather_schemas(entities):
    return sorted({e["schema"] for e in entities if e.get("schema")})


def _gather_indexes(entities_sorted):
    out = []
    for e in entities_sorted:
        for ix in e.get("indexes") or []:
            out.append({
                "name": ix["name"],
                "schema": e["schema"],
                "table": e["table"],
                "columns": ix["columns"],
                "unique": bool(ix.get("unique")),
            })
    return out


_ON_DELETE_SQL = {
    "restrict": "RESTRICT",
    "cascade": "CASCADE",
    "set_null": "SET NULL",
    "no_action": "NO ACTION",
    "no action": "NO ACTION",
}


def _fk_columns(relation: dict):
    """Return FK column(s) as a list. Accepts:
    - nested {fk: {column: 'x'}}  → ['x']
    - nested {fk: {column: ['a','b']}} → ['a','b']
    - legacy flat {fk: 'x'} → ['x']
    """
    fk = relation.get("fk")
    if isinstance(fk, dict):
        col = fk.get("column")
    else:
        col = fk
    if col is None:
        return []
    if isinstance(col, list):
        return list(col)
    return [col]


def _fk_on_delete(relation: dict) -> str:
    fk = relation.get("fk")
    if isinstance(fk, dict) and fk.get("on_delete"):
        raw = fk["on_delete"]
    else:
        raw = relation.get("on_delete") or "restrict"
    return _ON_DELETE_SQL.get(str(raw).lower(), str(raw).upper())


def _gather_foreign_keys(blueprint: dict, by_name):
    """Identify which side actually owns the FK column(s).

    blueprint-spec convention: from=parent (1), to=child (N, holds FK).
    Legacy convention: from=child (N, holds FK), to=parent (1).
    Owner is whichever side has ALL fk_cols among its columns; fall back to
    `from` to preserve legacy behavior when neither has them.
    """
    fks = []
    for r in blueprint.get("relations") or []:
        a = by_name.get(r.get("from"))
        b = by_name.get(r.get("to"))
        if not a or not b:
            continue
        fk_cols = _fk_columns(r)
        if not fk_cols:
            continue
        a_names = {c.get("name") for c in (a.get("columns") or [])}
        b_names = {c.get("name") for c in (b.get("columns") or [])}
        if all(c in b_names for c in fk_cols) and not all(c in a_names for c in fk_cols):
            owner, parent = b, a
        else:
            owner, parent = a, b
        ref_pks = [c["name"] for c in parent.get("columns") or [] if c.get("pk")]
        if not ref_pks:
            continue
        # composite FK references composite PK — assume positional pairing
        ref_cols = ref_pks if len(fk_cols) > 1 else [ref_pks[0]]
        fks.append({
            "name": f"fk_{owner['table']}__{'_'.join(fk_cols)}",
            "src_schema": owner["schema"], "src_table": owner["table"],
            "columns": fk_cols,
            "ref_schema": parent["schema"], "ref_table": parent["table"],
            "ref_columns": ref_cols,
            "on_delete": _fk_on_delete(r),
        })
    return fks


def _gather_checks(blueprint: dict, by_name):
    """Read business rules. Supports both legacy `{name, applies_to, enforced_by}`
    and blueprint-spec `{id, text, enforced_by, source_concept, applies_to?}`."""
    chks = []
    for br in blueprint.get("business_rules") or []:
        expr = (br.get("enforced_by") or "").strip()
        if not expr:
            continue
        applies_to = br.get("applies_to")
        target = by_name.get(applies_to)
        if not target:
            continue
        chks.append({
            "name": br.get("name") or br.get("id") or "chk_rule",
            "schema": target["schema"],
            "table": target["table"],
            "expression": expr,
        })
    return chks


def generate_ddl(blueprint: dict, out_dir: pathlib.Path, dialect: str = "postgres") -> None:
    out_dir = pathlib.Path(out_dir)
    (out_dir / "migrations").mkdir(parents=True, exist_ok=True)
    d = get_dialect(dialect)
    env = _env(d.template_dir)

    entities_sorted = topo_sort(blueprint.get("entities", []), blueprint.get("relations", []))
    entities_render = [{**e, "columns": _normalize_columns(e, d)} for e in entities_sorted]
    schemas = _gather_schemas(entities_sorted)
    by_name = {e["name"]: e for e in entities_sorted}
    indexes = _gather_indexes(entities_sorted)
    fks = _gather_foreign_keys(blueprint, by_name)
    chks = _gather_checks(blueprint, by_name)

    (out_dir / "migrations" / "V001__create_schema.sql").write_text(
        env.get_template("schema.sql.j2").render(schemas=schemas), encoding="utf-8")
    (out_dir / "migrations" / "V002__create_tables.sql").write_text(
        env.get_template("tables.sql.j2").render(entities=entities_render), encoding="utf-8")
    (out_dir / "migrations" / "V003__create_indexes.sql").write_text(
        env.get_template("indexes.sql.j2").render(indexes=indexes), encoding="utf-8")
    (out_dir / "migrations" / "V004__create_constraints.sql").write_text(
        env.get_template("constraints.sql.j2").render(foreign_keys=fks, checks=chks), encoding="utf-8")
