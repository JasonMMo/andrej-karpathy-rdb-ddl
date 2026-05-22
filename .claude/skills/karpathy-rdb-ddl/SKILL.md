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

## Ownership & Self-Check (Phase A — 2026-05-22)

이 skill 은 **business-fullstack-creater 5축 책임표의 `ddl (Stage 2)` 축**을 담당. 활동 뷰는 `business-fullstack-creater/learn-log.md` §0.

- **깊이 누적 위치**: `catalogs/preset-catalog.yaml` + dialect 어댑터 (`scripts/dialect/postgres.py|hsqldb.py|mysql.py`)
- **단위 테스트**: `tests/` (pytest)
- **누적 트랩 (3)**: HSQLDB IDENTITY 0-base / SQL:2008 `LEAD` 예약어 / HSQLDB vs postgres-default schema 불일치
- **미해결 환류**: 없음
- **Self-check (Growth 종료 시)**: 새 dialect/preset 변경이 발생했다면 `learn-log.md` §0 ddl 행 + §2 (도메인) 또는 §4 (트랩) 한 줄 환류했는가?
