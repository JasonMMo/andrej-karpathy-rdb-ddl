"""Preset domain↔entity catalog.

`PRESETS` is loaded from `<repo_root>/catalogs/preset-catalog.yaml` at module
import time so users can extend the catalog without touching Python code.
The public API (the `PRESETS` name and `is_preset()` signature) is unchanged
to keep callers (ddl_compile, seed_gen, blueprint_spec tests) untouched.
"""
from pathlib import Path
import yaml

_CATALOG_PATH = Path(__file__).resolve().parent.parent / "catalogs" / "preset-catalog.yaml"


def _load_presets(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"preset catalog not found at {path}. "
            f"Create it with `version: 1` and a `domains:` map."
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level must be a mapping, got {type(data).__name__}")
    if data.get("version") != 1:
        raise ValueError(f"{path}: unsupported catalog version {data.get('version')!r} (expected 1)")
    domains = data.get("domains") or {}
    if not isinstance(domains, dict):
        raise ValueError(f"{path}: `domains` must be a mapping")
    out: dict[str, set[str]] = {}
    for dn, entities in domains.items():
        if entities is None:
            out[dn] = set()
            continue
        if not isinstance(entities, list):
            raise ValueError(f"{path}: domain {dn!r} entities must be a list")
        out[dn] = {str(e) for e in entities}
    return out


PRESETS: dict[str, set[str]] = _load_presets(_CATALOG_PATH)


def build_domain_index(blueprint: dict) -> dict:
    """blueprint['domains'][i]['entities'][] → {entity_name: [domain_name, ...]}.

    Returns empty dict if blueprint has no top-level `domains`. Use this so
    `is_preset` can resolve domain membership from blueprint-spec.md output."""
    idx: dict = {}
    for d in blueprint.get("domains") or []:
        dn = d.get("name")
        if not dn:
            continue
        for en in d.get("entities") or []:
            idx.setdefault(en, []).append(dn)
    return idx


def _domains(entity: dict, domain_index):
    if domain_index is not None:
        return list(domain_index.get(entity.get("name"), []))
    d = entity.get("domain")
    if d is None:
        return []
    if isinstance(d, str):
        return [d]
    return list(d)


def is_preset(entity: dict, domain_index=None) -> bool:
    if entity.get("preset"):
        return True
    name = entity.get("name")
    for domain in _domains(entity, domain_index):
        if name in PRESETS.get(domain, set()):
            return True
    return False
