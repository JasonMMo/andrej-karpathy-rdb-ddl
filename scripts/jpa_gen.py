import pathlib
from jinja2 import Environment, FileSystemLoader, StrictUndefined


TEMPLATE_ROOT = pathlib.Path(__file__).resolve().parent.parent / ".claude" / "skills" / "karpathy-rdb-ddl" / "templates"


_JAVA_TYPE = {
    "bigserial": "Long", "bigint": "Long", "integer": "Integer",
    "varchar": "String", "text": "String", "boolean": "Boolean",
    "timestamp": "LocalDateTime", "date": "LocalDate", "numeric": "BigDecimal",
}


def _pascal(name: str) -> str:
    return "".join(p.capitalize() for p in name.split("_"))


def _camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _java_type(sql_type: str) -> str:
    base = sql_type.split("(")[0].lower().strip()
    return _JAVA_TYPE.get(base, "String")


def generate_jpa(entities, package: str, out_dir: pathlib.Path) -> None:
    out_dir = pathlib.Path(out_dir)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_ROOT)),
        undefined=StrictUndefined,
        trim_blocks=False,
        lstrip_blocks=False,
        keep_trailing_newline=True,
    )
    tpl = env.get_template("entity.java.j2")
    for e in entities:
        cols_render = []
        for c in e.get("columns") or []:
            c2 = {
                **c,
                "java_type": _java_type(c.get("type", "")),
                "java_name": _camel(c.get("name", "")),
            }
            if None in c2:
                c2["nullable"] = c2.pop(None)
            if "null" in c2 and "nullable" not in c2:
                c2["nullable"] = c2.pop("null")
            c2.setdefault("pk", False)
            c2.setdefault("nullable", True)
            c2.setdefault("unique", False)
            cols_render.append(c2)
        types = {c["java_type"] for c in cols_render}
        pkg = package
        if "<schema>" in pkg:
            pkg = pkg.replace("<schema>", e["schema"])
        class_name = _pascal(e["name"])
        out_path = out_dir / "src" / "main" / "java" / pathlib.Path(*pkg.split("."))
        out_path.mkdir(parents=True, exist_ok=True)
        rendered = tpl.render(
            package=pkg, entity={**e, "columns": cols_render},
            class_name=class_name,
            has_timestamp="LocalDateTime" in types,
            has_date="LocalDate" in types,
            has_bigdecimal="BigDecimal" in types,
        )
        (out_path / f"{class_name}.java").write_text(rendered, encoding="utf-8")
