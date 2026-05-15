"""Preset domain↔entity catalog.

`PRESETS` is loaded from `<repo_root>/catalogs/preset-catalog.yaml` at module
import time so users can extend the catalog without touching Python code.
The public API (the `PRESETS` name and `is_preset()` signature) is unchanged
to keep callers (ddl_compile, seed_gen, blueprint_spec tests) untouched.

If a global catalog (`~/.karpathy-rdb/catalog/<domain>.seed.md`) exists for a
domain, its entities are merged into PRESETS at import time so Stage 2 picks
up entities that Stage 1's `/karpathy-rdb contribute` has accumulated. Local
catalog entries take precedence on overlap; global is additive.
"""
from pathlib import Path
import re
import yaml

_CATALOG_PATH = Path(__file__).resolve().parent.parent / "catalogs" / "preset-catalog.yaml"
_GLOBAL_CATALOG_DIR = Path.home() / ".karpathy-rdb" / "catalog"


def _parse_global_seed(seed_path: Path) -> set[str]:
    """Extract entity names from a contribute-emitted seed.md file.

    Format: ` ```yaml ... type: entity, name: <x> ... ``` ` blocks. Returns
    set of entity names. Malformed blocks are skipped (don't crash import).
    """
    if not seed_path.exists():
        return set()
    text = seed_path.read_text(encoding="utf-8")
    names: set[str] = set()
    for match in re.finditer(r"```yaml\n(.*?)\n```", text, re.DOTALL):
        try:
            block = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            continue
        if isinstance(block, dict) and block.get("type") == "entity" and block.get("name"):
            names.add(str(block["name"]))
    return names


def _merge_global_catalog(local: dict, global_dir: Path = _GLOBAL_CATALOG_DIR) -> dict:
    """Add entities from global per-domain seed.md files into the local map.

    Existing local domains are augmented (set union); new domains are added.
    Missing global directory is silently ignored — global is optional.
    """
    if not global_dir.exists():
        return local
    out = {dn: set(ents) for dn, ents in local.items()}
    for seed_path in global_dir.glob("*.seed.md"):
        domain = seed_path.name[: -len(".seed.md")]
        out.setdefault(domain, set()).update(_parse_global_seed(seed_path))
    return out


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


PRESETS: dict[str, set[str]] = _merge_global_catalog(_load_presets(_CATALOG_PATH))


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
