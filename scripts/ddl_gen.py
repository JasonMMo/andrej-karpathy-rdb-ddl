import pathlib
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from dialect import get_dialect
from toposort import topo_sort


TEMPLATE_ROOT = pathlib.Path(__file__).resolve().parent.parent / ".claude" / "skills" / "karpathy-rdb-ddl" / "templates"


def _env(dialect_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_ROOT / dialect_dir)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _normalize_columns(entity: dict, dialect) -> list:
    cols = []
    for c in entity.get("columns") or []:
        c2 = dict(c)
        raw_type = c.get("type", "").strip()
        base = raw_type.split("(")[0].lower()
        mapped = dialect.type_map.get(base, raw_type.upper())
        if "(" in raw_type and base in {"varchar", "numeric"}:
            mapped = mapped + raw_type[raw_type.index("("):]
        c2["sql_type"] = mapped
        # Ensure template attributes are defined to avoid StrictUndefined errors
        c2.setdefault("pk", False)
        c2.setdefault("null", True)
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


def _gather_foreign_keys(blueprint: dict, by_name):
    fks = []
    for r in blueprint.get("relations") or []:
        src = by_name.get(r.get("from"))
        dst = by_name.get(r.get("to"))
        if not src or not dst:
            continue
        ref_pk = next((c["name"] for c in dst.get("columns") or [] if c.get("pk")), None)
        if not ref_pk:
            continue
        fk_name = f"fk_{src['table']}_{r.get('fk', 'unknown')}"
        fks.append({
            "name": fk_name,
            "src_schema": src["schema"], "src_table": src["table"],
            "column": r.get("fk"),
            "ref_schema": dst["schema"], "ref_table": dst["table"],
            "ref_column": ref_pk,
            "on_delete": r.get("on_delete", "no action"),
        })
    return fks


def _gather_checks(blueprint: dict, by_name):
    chks = []
    for br in blueprint.get("business_rules") or []:
        expr = (br.get("enforced_by") or "").strip()
        if not expr:
            continue
        target = by_name.get(br.get("applies_to"))
        if not target:
            continue
        chks.append({
            "name": br["name"],
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
