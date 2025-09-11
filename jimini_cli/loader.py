import os, re, yaml
from typing import Dict, Tuple
from app.models import Rule

PACK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packs"))

def _load_yaml(path: str):
    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}
    return raw.get("rules", raw if isinstance(raw, list) else [])

def load_rules_from_file(path: str) -> Dict[str, Tuple[Rule, object]]:
    rules_list = _load_yaml(path)
    return _to_store(rules_list)

def load_rules_from_pack(pack: str, version: str = "v1") -> Dict[str, Tuple[Rule, object]]:
    # map short names → path
    pack_path = os.path.join(PACK_DIR, pack.lower(), f"{version}.yaml")
    if not os.path.exists(pack_path):
        raise FileNotFoundError(f"Rule pack not found: {pack} ({pack_path})")
    rules_list = _load_yaml(pack_path)
    return _to_store(rules_list)

def _to_store(rules_list):
    store = {}
    for item in rules_list:
        rule = Rule(**item)
        cregex = None
        if rule.pattern:
            cregex = re.compile(rule.pattern)
        store[rule.id] = (rule, cregex)
    return store
