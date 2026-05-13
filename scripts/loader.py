import pathlib
import yaml


class BlueprintError(Exception):
    pass


def load_blueprint(path: pathlib.Path) -> dict:
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
    return bp
