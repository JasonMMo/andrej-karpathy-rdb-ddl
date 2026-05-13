# Install for AI agents

This plugin is consumed automatically by Claude Code after install. The 5-phase install protocol below assumes the user has already produced `_blueprint.yaml` from Stage 1.

## Phase 1 — Verify Stage 1 output

Ask the user to confirm path to `<wiki>/_blueprint.yaml`. Verify:
- file exists
- `version: 1`
- `validation.passed: true`

If any check fails, instruct the user to re-run `/karpathy-rdb compile` in Stage 1.

## Phase 2 — Plugin install (one-time)

```
git clone <repo> ~/.claude/plugins/andrej-karpathy-rdb-ddl
```

`plugin.json` registers commands and skills automatically.

## Phase 3 — Pick dialect

Ask user: PostgreSQL (default, production) or HSQLDB (embedded testing). Save to project CLAUDE.md.

## Phase 4 — Run compile

```
/rdb-ddl-compile <wiki_path> --out ./db --package com.example.<schema> --dialect <chosen>
```

## Phase 5 — Verify + handoff

Confirm `ddl-report.md` shows ERROR: 0. List generated files. Tell user the `./db/` directory is the input for Stage 3 `/nexacro-fullstack-starter`.
