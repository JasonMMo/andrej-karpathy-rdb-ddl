# andrej-karpathy-rdb-ddl

`business-fullstack-creater` 파이프라인의 2단계.

1단계 `andrej-karpathy-rdb-skill`의 산출물 `_blueprint.yaml`을 입력받아 다음을 생성합니다:

- PostgreSQL / HSQLDB DDL
- Flyway 마이그레이션 (`V001~V004__*.sql`)
- JPA Entity Java 소스 (Lombok, JDK 11+ 호환)
- preset 엔티티에 대한 seed SQL

## 빠른 시작

```
/rdb-ddl-compile <wiki_경로> --out ./db --dialect postgres
```

## 지원 dialect

- `postgres` (기본): PostgreSQL 15+
- `hsqldb`: HSQLDB 2.7+ (embedded/test 용)

## 파이프라인 위치

```
1단계 (andrej-karpathy-rdb-skill)  →  _blueprint.yaml
                                       ↓
2단계 (andrej-karpathy-rdb-ddl)    →  DDL + JPA + seed   ← 현재
                                       ↓
3단계 (/nexacro-fullstack-starter) →  Spring Boot 스캐폴드
```
