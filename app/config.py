from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel


class AppConfig(BaseModel):
    """Lightweight application configuration used by tests and legacy callers."""

    api_key: str = "changeme"
    shadow_mode: bool = False
    webhook_url: Optional[str] = None
    otel_endpoint: Optional[str] = None
    rules_path: str = "policy_rules.yaml"
    audit_log_path: str = "logs/audit.jsonl"

    @classmethod
    def from_env(cls, base: Optional["AppConfig"] = None) -> "AppConfig":
        """Create configuration populated from environment variables."""

        data = base.to_dict() if base else {}
        env_map = {
            "JIMINI_API_KEY": "api_key",
            "JIMINI_SHADOW": "shadow_mode",
            "WEBHOOK_URL": "webhook_url",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "otel_endpoint",
            "JIMINI_RULES_PATH": "rules_path",
            "AUDIT_LOG_PATH": "audit_log_path",
        }

        for env_name, attr in env_map.items():
            value = os.getenv(env_name)
            if value is None:
                continue

            if attr == "shadow_mode":
                data[attr] = value.lower() in {"1", "true", "yes", "on"}
            else:
                data[attr] = value

        return cls(**data)

    def validate(self) -> bool:
        """Return True when required fields are populated."""

        if not self.api_key or not self.api_key.strip():
            return False
        if not self.rules_path or not self.rules_path.strip():
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """Update configuration in place with basic type coercion."""

        current_keys = set(self.model_dump().keys())
        for key, value in updates.items():
            if key not in current_keys:
                continue
            if key == "shadow_mode" and isinstance(value, str):
                coerced = value.lower() in {"1", "true", "yes", "on"}
            else:
                coerced = value
            setattr(self, key, coerced)


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
            if not isinstance(data, dict):
                return {}
            return data
    except yaml.YAMLError:
        return {}


def load_config(path: Optional[str] = None) -> AppConfig:
    """Load configuration from YAML and environment variables."""

    config_path = Path(path) if path else Path("jimini.config.yaml")
    base_data = _load_yaml(config_path)
    base_config = AppConfig(**base_data)
    return AppConfig.from_env(base_config)


_config_cache: Optional[AppConfig] = None


def get_config(path: Optional[str] = None, force_reload: bool = False) -> AppConfig:
    """Return a cached configuration instance, reloading when requested."""

    global _config_cache
    if force_reload or _config_cache is None:
        _config_cache = load_config(path)
    return _config_cache


def set_config(config: AppConfig) -> None:
    """Override the cached configuration, primarily used in tests."""

    global _config_cache
    _config_cache = config


def update_config(config: AppConfig, updates: Dict[str, Any]) -> AppConfig:
    """Return a new AppConfig with updates applied."""

    new_values = config.to_dict()
    new_values.update(updates)
    updated = AppConfig(**new_values)
    set_config(updated)
    return updated


def get_config_value(config: AppConfig, key: str, default: Any = None) -> Any:
    """Helper for safely reading configuration attributes."""

    return getattr(config, key, default)
