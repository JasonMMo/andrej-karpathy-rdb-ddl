from collections import defaultdict, deque
from typing import List, Dict


class CycleError(Exception):
    pass


def topo_sort(entities: List[dict], relations: List[dict]) -> List[dict]:
    by_name: Dict[str, dict] = {e["name"]: e for e in entities}
    indegree: Dict[str, int] = {name: 0 for name in by_name}
    out: Dict[str, set] = defaultdict(set)
    for r in relations:
        frm, to = r["from"], r["to"]
        if frm == to:  # self-reference, ignore for ordering
            continue
        if frm not in by_name or to not in by_name:
            continue
        if frm in out[to]:
            continue
        out[to].add(frm)
        indegree[frm] += 1
    ready = deque(sorted(name for name, d in indegree.items() if d == 0))
    result = []
    while ready:
        name = ready.popleft()
        result.append(by_name[name])
        for downstream in sorted(out[name]):
            indegree[downstream] -= 1
            if indegree[downstream] == 0:
                ready.append(downstream)
    if len(result) != len(by_name):
        remaining = set(by_name) - {e["name"] for e in result}
        raise CycleError(f"cycle detected among: {sorted(remaining)}")
    return result
