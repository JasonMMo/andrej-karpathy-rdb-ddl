#!/usr/bin/env python3
import argparse
import pathlib
import sys
import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from loader import load_blueprint, BlueprintError
from revalidator import revalidate
from ddl_gen import generate_ddl
from jpa_gen import generate_jpa
from seed_gen import generate_seed


def _resolve_package(template: str, schema: str) -> str:
    return template.replace("<schema>", schema)


def _write_report(out_dir: pathlib.Path, blueprint: dict, diags: list, dialect: str, stats: dict) -> None:
    errors = [d for d in diags if d["severity"] == "ERROR"]
    warns = [d for d in diags if d["severity"] == "WARN"]
    lines = [
        "# DDL Compile Report",
        f"- timestamp: {datetime.datetime.now().isoformat()}",
        f"- dialect: {dialect}",
        f"- project: {blueprint.get('project')}",
        f"- entities: {stats['entities']}, relations: {stats['relations']}, schemas: {stats['schemas']}",
        "",
        "## Revalidation",
        f"- ERROR: {len(errors)}",
        f"- WARN: {len(warns)}",
    ]
    if warns:
        lines.append("")
        lines.append("### Warnings")
        for w in warns:
            lines.append(f"- {w['code']}: {w['message']}")
    if errors:
        lines.append("")
        lines.append("### Errors")
        for e in errors:
            lines.append(f"- {e['code']}: {e['message']}")
    lines.append("")
    lines.append("## Outputs")
    lines.append(f"- migrations: 4 files")
    lines.append(f"- jpa: {stats['entities']} entity files")
    lines.append(f"- seed: {stats['seeds']} preset files")
    lines.append("")
    lines.append("## Next")
    lines.append("Hand off `db/` to Stage 3 (/nexacro-fullstack-starter).")
    (out_dir / "ddl-report.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ddl_compile")
    ap.add_argument("blueprint", help="path to _blueprint.yaml")
    ap.add_argument("--out", default="./db", help="output directory (default ./db)")
    ap.add_argument("--package", default="com.example.<schema>", help="Java package template")
    ap.add_argument("--dialect", default="postgres", choices=["postgres", "hsqldb"])
    args = ap.parse_args(argv)

    try:
        bp = load_blueprint(pathlib.Path(args.blueprint))
    except BlueprintError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    diags = revalidate(bp, dialect=args.dialect)
    errors = [d for d in diags if d["severity"] == "ERROR"]
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if errors:
        stats = {"entities": len(bp.get("entities") or []),
                 "relations": len(bp.get("relations") or []),
                 "schemas": len({e["schema"] for e in bp.get("entities") or [] if e.get("schema")}),
                 "seeds": 0}
        _write_report(out_dir, bp, diags, args.dialect, stats)
        for e in errors:
            print(f"ERROR {e['code']}: {e['message']}", file=sys.stderr)
        return 1

    try:
        generate_ddl(bp, out_dir, dialect=args.dialect)
        for e in bp.get("entities") or []:
            pkg = _resolve_package(args.package, e.get("schema", "default"))
            generate_jpa([e], package=pkg, out_dir=out_dir)
        generate_seed(bp.get("entities") or [], out_dir, dialect=args.dialect)
    except Exception as e:
        print(f"ERROR: template/IO failure: {e}", file=sys.stderr)
        return 3

    from preset_catalog import is_preset
    stats = {
        "entities": len(bp.get("entities") or []),
        "relations": len(bp.get("relations") or []),
        "schemas": len({e["schema"] for e in bp.get("entities") or [] if e.get("schema")}),
        "seeds": sum(1 for e in bp.get("entities") or [] if is_preset(e)),
    }
    _write_report(out_dir, bp, diags, args.dialect, stats)
    print(f"OK: wrote {out_dir} (dialect={args.dialect})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
