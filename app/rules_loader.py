import os
import yaml
import re
from typing import List
from app.models import Rule

rules_store: List[Rule] = []


def load_token_quotas(quota_path: str = "token_quotas.yaml"):
    """
    Load token quotas from YAML configuration.
    
    Args:
        quota_path: Path to token quotas YAML file
    """
    if not os.path.exists(quota_path):
        print(f"Info: Token quotas file {quota_path} not found, using defaults")
        return
    
    try:
        from app.token_limiter import token_limiter, TokenQuota
        
        with open(quota_path, "r") as f:
            config = yaml.safe_load(f)
        
        # Set default quota
        if "default" in config:
            default = config["default"]
            token_limiter.default_quota = TokenQuota(
                tokens_per_minute=default.get("tokens_per_minute", 10_000),
                tokens_per_hour=default.get("tokens_per_hour", 500_000),
                tokens_per_day=default.get("tokens_per_day", 10_000_000)
            )
        
        # Load tier definitions
        tiers = {}
        if "tiers" in config:
            for tier_name, tier_config in config["tiers"].items():
                tiers[tier_name] = TokenQuota(
                    tokens_per_minute=tier_config.get("tokens_per_minute", 10_000),
                    tokens_per_hour=tier_config.get("tokens_per_hour", 500_000),
                    tokens_per_day=tier_config.get("tokens_per_day", 10_000_000)
                )
        
        # Assign quotas to API keys
        if "api_keys" in config:
            for api_key, tier_name in config["api_keys"].items():
                if tier_name in tiers:
                    token_limiter.set_quota(api_key, tiers[tier_name])
                elif tier_name == "default":
                    token_limiter.set_quota(api_key, token_limiter.default_quota)
        
        print(f"Loaded token quotas from {quota_path}")
        print(f"  Default: {token_limiter.default_quota.tokens_per_minute} TPM")
        print(f"  Configured API keys: {len(config.get('api_keys', {}))}")
        
    except Exception as e:
        print(f"Error loading token quotas: {e}")


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

        # Update the global list in-place so imports see the changes
        rules_store.clear()
        rules_store.extend(rules)
        print(f"Loaded {len(rules)} rules from {rules_path}")
    except Exception as e:
        print(f"Error loading rules: {e}")
