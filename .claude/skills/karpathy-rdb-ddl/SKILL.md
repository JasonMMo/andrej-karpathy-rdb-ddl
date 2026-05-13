---
name: karpathy-rdb-ddl
description: Stage 2 — generates PostgreSQL/HSQLDB DDL, Flyway migrations, JPA Entity Java, and seed SQL from Stage 1 _blueprint.yaml
---

# karpathy-rdb-ddl

Stage 2 of the business-fullstack-creater pipeline. Consumes the validated `_blueprint.yaml` from Stage 1 (`andrej-karpathy-rdb-skill`) and produces:

- PostgreSQL or HSQLDB DDL split into Flyway migrations V001~V004
- JPA Entity Java sources (Lombok, JDK 11+ compatible)
- Seed SQL for preset entities (3 rows each)
- `ddl-report.md` with V001~V005 revalidation results

## Command

`/rdb-ddl-compile <wiki_path> [--out <dir>] [--package <pkg>] [--dialect postgres|hsqldb]`

See `references/ddl-spec.md` for output contract.
See `references/validation-codes.md` for V001~V010 reference.
