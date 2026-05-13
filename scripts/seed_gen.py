import pathlib
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from dialect import get_dialect
from preset_catalog import is_preset


TEMPLATE_ROOT = pathlib.Path(__file__).resolve().parent.parent / ".claude" / "skills" / "karpathy-rdb-ddl" / "templates"


def _sample_value(col: dict, row_idx: int) -> str:
    base = col.get("type", "").split("(")[0].lower()
    if base in {"bigserial", "bigint", "integer", "numeric"}:
        return str(row_idx + 1)
    if base == "boolean":
        return "TRUE"
    if base in {"timestamp", "date"}:
        return "CURRENT_TIMESTAMP" if base == "timestamp" else "CURRENT_DATE"
    return f"'sample{row_idx + 1}'"


def generate_seed(entities, out_dir: pathlib.Path, dialect: str = "postgres") -> None:
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
        if not is_preset(e):
            continue
        non_pk_cols = [c for c in e.get("columns") or [] if not c.get("pk")]
        if not non_pk_cols:
            continue
        col_names = [c["name"] for c in non_pk_cols]
        pk_col = next((c["name"] for c in e.get("columns") or [] if c.get("pk")), "id")
        rows = [[_sample_value(c, i) for c in non_pk_cols] for i in range(3)]
        rendered = tpl.render(entity=e, columns=col_names, rows=rows, pk_column=pk_col)
        (out_dir / "seed" / f"01_{e['table']}_sample.sql").write_text(rendered, encoding="utf-8")
