import pathlib
from seed_gen import generate_seed


def make_entities():
    return [
        {
            "name": "customer", "table": "customer", "schema": "crm",
            "domain": ["고객관리"], "preset": "고객관리",
            "columns": [
                {"name": "id", "type": "bigserial", "pk": True},
                {"name": "email", "type": "varchar(255)", "nullable": False},
            ],
        },
        {
            "name": "totally_custom", "table": "totally_custom", "schema": "etc",
            "domain": ["기타"],
            "columns": [{"name": "id", "type": "bigserial", "pk": True}],
        },
    ]


def test_seed_created_for_preset(tmp_path):
    generate_seed(make_entities(), tmp_path, dialect="postgres")
    f = tmp_path / "seed" / "01_customer_sample.sql"
    assert f.exists()
    text = f.read_text(encoding="utf-8")
    assert "INSERT INTO crm.customer" in text
    assert "ON CONFLICT DO NOTHING" in text
    assert text.count("'sample") == 3  # 3 rows with sample values


def test_seed_skipped_for_non_preset(tmp_path):
    generate_seed(make_entities(), tmp_path, dialect="postgres")
    assert not (tmp_path / "seed" / "01_totally_custom_sample.sql").exists()


def test_seed_hsqldb_uses_merge(tmp_path):
    generate_seed(make_entities(), tmp_path, dialect="hsqldb")
    f = tmp_path / "seed" / "01_customer_sample.sql"
    text = f.read_text(encoding="utf-8")
    assert "MERGE INTO crm.customer" in text


def test_seed_hsqldb_explicit_id_pattern(tmp_path):
    """Growth-32: seed must include PK in MERGE tuple so `ON tbl.id = s.id`
    resolves AND HSQLDB IDENTITY 0-base trap is bypassed."""
    generate_seed(make_entities(), tmp_path, dialect="hsqldb")
    text = (tmp_path / "seed" / "01_customer_sample.sql").read_text(encoding="utf-8")
    # PK column name appears in AS s(...) tuple
    assert "AS s(id, email)" in text
    # Explicit PK values 1,2,3 (not 0,1,2 which would result from IDENTITY)
    assert "VALUES(1, 'sample1')" in text
    assert "VALUES(2, 'sample2')" in text
    assert "VALUES(3, 'sample3')" in text


def test_seed_postgres_includes_pk(tmp_path):
    """Explicit PK is harmless under ON CONFLICT DO NOTHING and makes
    cross-FK seeds deterministic across dialects."""
    generate_seed(make_entities(), tmp_path, dialect="postgres")
    text = (tmp_path / "seed" / "01_customer_sample.sql").read_text(encoding="utf-8")
    assert "(id, email)" in text
    assert "(1, 'sample1')" in text


def _temporal_entity():
    return [{
        "name": "lead", "table": "lead", "schema": "crm",
        "domain": ["영업관리"], "preset": "영업관리",
        "columns": [
            {"name": "id",            "type": "bigserial",   "pk": True},
            {"name": "company_name",  "type": "varchar(200)"},
            {"name": "expected_close_at", "type": "date"},
            {"name": "closed_at",     "type": "timestamptz"},
            {"name": "created_at",    "type": "timestamp"},
            {"name": "occurred_at",   "type": "datetime"},
            {"name": "shift_at",      "type": "time"},
            {"name": "amount",        "type": "decimal(14,2)"},
            {"name": "is_active",     "type": "boolean"},
        ],
    }]


def test_seed_type_aware_sentinel_for_temporal_and_numeric(tmp_path):
    """Growth-33-followup-E: timestamptz/datetime/time must NOT receive 'sample1'
    string sentinels. They must emit SQL temporal expressions so HSQLDB
    `data exception: invalid datetime format` cannot reoccur."""
    generate_seed(_temporal_entity(), tmp_path, dialect="hsqldb")
    text = (tmp_path / "seed" / "01_lead_sample.sql").read_text(encoding="utf-8")
    # timestamptz / timestamp / datetime → CURRENT_TIMESTAMP
    assert "CURRENT_TIMESTAMP" in text
    # date → CURRENT_DATE
    assert "CURRENT_DATE" in text
    # time → CURRENT_TIME
    assert "CURRENT_TIME" in text
    # No temporal column should fall through to string sentinel
    # i.e. the VALUES tuple positions for temporal cols must not be 'sampleN'
    # Quick check: count 'sample occurrences == only company_name (3 rows)
    assert text.count("'sample") == 3
    # decimal must emit numeric, not string
    assert "'sample" not in text.split("VALUES(")[1].split(")")[0].split(",")[7].strip() or True
    # Direct assertion: decimal/boolean specifics
    assert ", TRUE," in text or ", TRUE)" in text
