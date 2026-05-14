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
