import os
import yaml
import re
from typing import List
from app.models import Rule

rules_store: List[Rule] = []


def load_rules(rules_path: str):
    """Load rules from a YAML file and compile regex patterns"""
    global rules_store

    if not os.path.exists(rules_path):
        print(f"Warning: Rules file {rules_path} not found")
        return

    try:
        with open(rules_path, "r") as f:
            yaml_content = yaml.safe_load(f)

        rules = []
        rule_list = (
            yaml_content.get("rules", [])
            if isinstance(yaml_content, dict)
            else yaml_content
        )
        for rule_dict in rule_list:
            rule = Rule(**rule_dict)

            # Compile regex pattern if present
            if rule.pattern:
                try:
                    rule.compiled_pattern = re.compile(rule.pattern)
                except re.error as e:
                    print(f"Error compiling regex for rule {rule.id}: {e}")

            rules.append(rule)

        rules_store.clear()
        rules_store.extend(rules)
        print(f"Loaded {len(rules)} rules from {rules_path}")
    except Exception as e:
        print(f"Error loading rules: {e}")
