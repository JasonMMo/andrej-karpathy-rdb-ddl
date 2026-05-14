import pathlib
import re
from jpa_gen import generate_jpa


def make_entities():
    return [{
        "name": "customer", "table": "customer", "schema": "crm",
        "columns": [
            {"name": "id", "type": "bigserial", "pk": True, "nullable": False},
            {"name": "email", "type": "varchar(255)", "nullable": False, "unique": True},
            {"name": "created_at", "type": "timestamp", "nullable": False},
        ],
    }]


def test_jpa_file_created(tmp_path):
    generate_jpa(make_entities(), package="com.example.crm", out_dir=tmp_path)
    f = tmp_path / "src" / "main" / "java" / "com" / "example" / "crm" / "Customer.java"
    assert f.exists()


def test_jpa_has_lombok_annotations(tmp_path):
    generate_jpa(make_entities(), package="com.example.crm", out_dir=tmp_path)
    text = (tmp_path / "src" / "main" / "java" / "com" / "example" / "crm" / "Customer.java").read_text()
    assert "@Data" in text
    assert "@NoArgsConstructor" in text
    assert "@AllArgsConstructor" in text
    assert "@Table(name = \"customer\", schema = \"crm\")" in text


def test_jpa_no_jdk17_syntax(tmp_path):
    generate_jpa(make_entities(), package="com.example.crm", out_dir=tmp_path)
    text = (tmp_path / "src" / "main" / "java" / "com" / "example" / "crm" / "Customer.java").read_text()
    assert not re.search(r"\brecord\s+\w+", text)
    assert "sealed " not in text
    assert "->" not in text


def test_jpa_camelcase_field_names(tmp_path):
    generate_jpa(make_entities(), package="com.example.crm", out_dir=tmp_path)
    text = (tmp_path / "src" / "main" / "java" / "com" / "example" / "crm" / "Customer.java").read_text()
    assert "private LocalDateTime createdAt;" in text


def test_jpa_id_annotation(tmp_path):
    generate_jpa(make_entities(), package="com.example.crm", out_dir=tmp_path)
    text = (tmp_path / "src" / "main" / "java" / "com" / "example" / "crm" / "Customer.java").read_text()
    assert "@Id" in text
    assert "GenerationType.IDENTITY" in text
