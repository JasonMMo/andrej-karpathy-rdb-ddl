---
name: rdb-ddl-compile
description: Stage 2 — generate PostgreSQL/HSQLDB DDL + Flyway + JPA + seed from _blueprint.yaml
argument-hint: <wiki_path> [--out <dir>] [--package <pkg>] [--dialect postgres|hsqldb]
---

# /rdb-ddl-compile

Compile Stage 1 wiki (`<wiki_path>/_blueprint.yaml`) into DDL artifacts.

## Usage

```
/rdb-ddl-compile <wiki_path> [--out <output_dir>] [--package <java_pkg>] [--dialect <postgres|hsqldb>]
```

## Defaults

- `--out`: `./db/`
- `--package`: `com.example.<schema>` (the literal substring `<schema>` is replaced per entity)
- `--dialect`: `postgres`

## Behavior

1. Verify `<wiki_path>/_blueprint.yaml` exists; abort with guidance if missing.
2. Run: `python scripts/ddl_compile.py <wiki>/_blueprint.yaml --out <out> --package <pkg> --dialect <dialect>`
3. Exit 0 → print artifact paths + `ddl-report.md`. Non-zero → surface `ddl-report.md` location and stderr.

## Exit codes

- 0: success
- 1: Stage 1 validation failed OR revalidation ERROR
- 2: file IO failure
- 3: template rendering failure
