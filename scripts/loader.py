import pathlib
import re
from typing import Optional

import yaml


class BlueprintError(Exception):
    pass


_GLOBAL_CATALOG_DIR = pathlib.Path.home() / ".karpathy-rdb" / "catalog"


def _find_catalog_entity(name: str, catalog_dir: pathlib.Path = _GLOBAL_CATALOG_DIR) -> Optional[dict]:
    """Search *.seed.md files in catalog_dir for an entity block matching name."""
    if not catalog_dir.exists():
        return None
    for seed_path in catalog_dir.glob("*.seed.md"):
        text = seed_path.read_text(encoding="utf-8")
        for match in re.finditer(r"```yaml\n(.*?)\n```", text, re.DOTALL):
            try:
                block = yaml.safe_load(match.group(1))
            except yaml.YAMLError:
                continue
            if isinstance(block, dict) and block.get("type") == "entity" and block.get("name") == name:
                return block
    return None


def _resolve_extends(entity: dict, catalog_dir: pathlib.Path = _GLOBAL_CATALOG_DIR) -> dict:
    """Merge base entity from global catalog; current entity fields override base.

    Raises BlueprintError if extends is set but the named entity is not found.
    """
    extends_name = entity.get("extends")
    if not extends_name:
        return entity
    base = _find_catalog_entity(str(extends_name), catalog_dir)
    if base is None:
        raise BlueprintError(
            f"entity {entity.get('name')!r}: extends={extends_name!r} not found in global catalog "
            f"({catalog_dir}). Run /karpathy-rdb contribute to populate the catalog first."
        )
    merged: dict = {**base, **entity}
    for key in ("columns", "indexes", "constraints"):
        base_items = base.get(key) or []
        curr_items = entity.get(key) or []
        if not curr_items:
            merged[key] = base_items
        elif not base_items:
            merged[key] = curr_items
        else:
            # Override base items by name; current entity wins on collision
            combined = {item.get("name"): item for item in base_items if isinstance(item, dict)}
            for item in curr_items:
                if isinstance(item, dict):
                    combined[item.get("name")] = item
            merged[key] = list(combined.values())
    merged.pop("extends", None)
    return merged


def load_blueprint(path: pathlib.Path, catalog_dir: pathlib.Path = _GLOBAL_CATALOG_DIR) -> dict:
    path = pathlib.Path(path)
    if not path.exists():
        raise BlueprintError(f"blueprint not found: {path}")
    try:
        bp = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise BlueprintError(f"malformed yaml: {e}") from e
    if not isinstance(bp, dict):
        raise BlueprintError("blueprint root must be a mapping")
    if bp.get("version") != 1:
        raise BlueprintError(f"unsupported blueprint version: {bp.get('version')}")
    validation = bp.get("validation") or {}
    if not validation.get("passed"):
        raise BlueprintError("Stage 1 validation failed — run /karpathy-rdb compile again")
    bp.setdefault("entities", [])
    bp.setdefault("relations", [])
    bp.setdefault("business_rules", [])
    bp["entities"] = [_resolve_extends(e, catalog_dir) for e in bp["entities"]]
    return bp
