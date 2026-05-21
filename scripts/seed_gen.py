import pathlib
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from dialect import get_dialect
from preset_catalog import is_preset


TEMPLATE_ROOT = pathlib.Path(__file__).resolve().parent.parent / ".claude" / "skills" / "karpathy-rdb-ddl" / "templates"


def _sample_value(col: dict, row_idx: int) -> str:
    base = col.get("type", "").split("(")[0].lower()
    if base in {"bigserial", "serial", "bigint", "integer", "int", "int2", "int4", "int8",
                "smallint", "numeric", "decimal", "real", "double", "float"}:
        return str(row_idx + 1)
    if base == "boolean":
        return "TRUE"
    if base in {"timestamp", "timestamptz", "datetime"}:
        return "CURRENT_TIMESTAMP"
    if base == "date":
        return "CURRENT_DATE"
    if base in {"time", "timetz"}:
        return "CURRENT_TIME"
    return f"'sample{row_idx + 1}'"


def generate_seed(entities, out_dir: pathlib.Path, dialect: str = "postgres",
                  domain_index=None) -> None:
    out_dir = pathlib.Path(out_dir)
    (out_dir / "seed").mkdir(parents=True, exist_ok=True)
    d = get_dialect(dialect)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_ROOT / d.template_dir)),
        undefined=StrictUndefined,
        trim_blocks=True, lstrip_blocks=True,
    )
    if d.idempotent_insert == "MERGE":
        env.filters["insert_prefix"] = lambda name, prefix: f"{prefix}{name}"
    tpl = env.get_template("seed.sql.j2")

    for e in entities:
        if not is_preset(e, domain_index):
            continue
        all_cols = list(e.get("columns") or [])
        non_pk_cols = [c for c in all_cols if not c.get("pk")]
        if not non_pk_cols:
            continue
        # Include PK in seed tuple so HSQLDB MERGE `ON tbl.id = s.id` resolves
        # and IDENTITY 0-base trap is bypassed across all dialects (Growth-32).
        seed_cols = all_cols
        col_names = [c["name"] for c in seed_cols]
        pk_col = next((c["name"] for c in seed_cols if c.get("pk")), "id")
        rows = [[_sample_value(c, i) for c in seed_cols] for i in range(3)]
        rendered = tpl.render(entity=e, columns=col_names, rows=rows, pk_column=pk_col)
        (out_dir / "seed" / f"01_{e['table']}_sample.sql").write_text(rendered, encoding="utf-8")
