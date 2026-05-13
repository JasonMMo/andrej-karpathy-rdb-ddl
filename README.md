# andrej-karpathy-rdb-ddl

Stage 2 of the `business-fullstack-creater` pipeline.

Converts the Stage 1 `_blueprint.yaml` (from `andrej-karpathy-rdb-skill`) into:

- PostgreSQL or HSQLDB DDL
- Flyway-compatible migrations (`V001~V004__*.sql`)
- JPA Entity Java sources (Lombok, JDK 11+ compatible)
- Seed SQL for preset entities

Korean version: [README.ko.md](README.ko.md)
Install for AI agents: [INSTALL-FOR-AI.md](INSTALL-FOR-AI.md)

## Quick start

```
/rdb-ddl-compile <wiki_path> --out ./db --dialect postgres
```

## Pipeline position

```
Stage 1 (andrej-karpathy-rdb-skill)  →  _blueprint.yaml
                                          ↓
Stage 2 (andrej-karpathy-rdb-ddl)    →  DDL + JPA + seed   ← you are here
                                          ↓
Stage 3 (/nexacro-fullstack-starter) →  Spring Boot scaffold
```
