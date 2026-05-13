# Validation Codes (Stage 2 re-runs V001~V005 at DDL level)

| Code | Check | Severity | On fail |
|---|---|---|---|
| V001 | Every entity has a PK column (`pk: true`) | ERROR | abort |
| V002 | Every relation.to exists, target has PK, FK column type matches | ERROR | abort |
| V003 | Identifiers are snake_case, not reserved, ≤63 chars | ERROR | abort |
| V004 | entity.schema present; cross-schema FK declared | ERROR | abort |
| V005 | `business_rules[*].enforced_by` SQL parses for target dialect | WARN | skip that CHECK, log to report |
