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


def generate_ddl(blueprint: dict, out_dir: pathlib.Path, dialect: str = "postgres") -> None:
    out_dir = pathlib.Path(out_dir)
    (out_dir / "migrations").mkdir(parents=True, exist_ok=True)
    d = get_dialect(dialect)
    env = _env(d.template_dir)

    entities_sorted = topo_sort(blueprint.get("entities", []), blueprint.get("relations", []))
    entities_render = [{**e, "columns": _normalize_columns(e, d)} for e in entities_sorted]
    schemas = _gather_schemas(entities_sorted)

    (out_dir / "migrations" / "V001__create_schema.sql").write_text(
        env.get_template("schema.sql.j2").render(schemas=schemas), encoding="utf-8")
    (out_dir / "migrations" / "V002__create_tables.sql").write_text(
        env.get_template("tables.sql.j2").render(entities=entities_render), encoding="utf-8")
