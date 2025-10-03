import os
from dotenv import load_dotenv
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field

load_dotenv()

API_KEY = os.getenv("JIMINI_API_KEY", "changeme")
RULES_PATH = os.getenv("JIMINI_RULES_PATH", "policy_rules.yaml")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", None)


class NotifierConfig(BaseModel):
    enabled: bool = False
    webhook_url: Optional[str] = None
    channel: Optional[str] = None
    username: Optional[str] = None
    icon_emoji: Optional[str] = None


class JsonlConfig(BaseModel):
    enabled: bool = True
    path: str = "logs/jimini_events.jsonl"


class SplunkHECConfig(BaseModel):
    enabled: bool = False
    url: Optional[str] = None
    token: Optional[str] = None
    sourcetype: str = "jimini:event"
    verify_tls: bool = True


class ElasticConfig(BaseModel):
    enabled: bool = False
    url: Optional[str] = None
    basic_auth_user: Optional[str] = None
    basic_auth_pass: Optional[str] = None
    verify_tls: bool = True


class OtelConfig(BaseModel):
    enabled: bool = False
    endpoint: Optional[str] = None
    service_name: str = "jimini"
    resource: Dict[str, str] = Field(default_factory=lambda: {"environment": "dev"})


class SiemConfig(BaseModel):
    jsonl: JsonlConfig = Field(default_factory=JsonlConfig)
    splunk_hec: SplunkHECConfig = Field(default_factory=SplunkHECConfig)
    elastic: ElasticConfig = Field(default_factory=ElasticConfig)


class NotifiersConfig(BaseModel):
    slack: NotifierConfig = Field(default_factory=NotifierConfig)
    teams: NotifierConfig = Field(default_factory=NotifierConfig)


class AppConfig(BaseModel):
    env: str = "dev"
    shadow_mode: bool = False
    shadow_overrides: List[str] = Field(default_factory=list)
    audit_log_path: str = "logs/audit.jsonl"


class PrivacySettings(BaseModel):
    retention_days: int = 365
    auto_purge: bool = True
    anonymize_pii: bool = True


class JiminiConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    notifiers: NotifiersConfig = Field(default_factory=NotifiersConfig)
    siem: SiemConfig = Field(default_factory=SiemConfig)
    otel: OtelConfig = Field(default_factory=OtelConfig)
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)
    
    @property
    def audit_log_path(self) -> str:
        """Get audit log path from app config"""
        return self.app.audit_log_path


_config_instance = None


def _resolve_env_vars(value: str) -> str:
    """Resolve environment variables in string values like ${VAR_NAME}"""
    if not isinstance(value, str) or "${" not in value:
        return value

    import re

    pattern = r"\${([A-Za-z0-9_]+)}"

    def replace_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, f"${{{var_name}}}")

    return re.sub(pattern, replace_var, value)


def _process_dict_env_vars(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively process all string values in dict for env var substitution"""
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = _process_dict_env_vars(value)
        elif isinstance(value, list):
            result[key] = [
                _resolve_env_vars(v) if isinstance(v, str) else v for v in value
            ]
        elif isinstance(value, str):
            result[key] = _resolve_env_vars(value)
        else:
            result[key] = value
    return result


def get_config() -> JiminiConfig:
    """Get the application configuration, loading it if necessary"""
    global _config_instance

    if _config_instance is not None:
        return _config_instance

    # Look for jimini.config.yaml in the current directory or parent directories
    config_data = {}
    config_paths = [
        Path("jimini.config.yaml"),
        Path("config/jimini.config.yaml"),
        Path.home() / ".jimini/config.yaml",
    ]

    for path in config_paths:
        if path.exists():
            with open(path, "r") as f:
                config_data = yaml.safe_load(f)
            break

    # Process any environment variables in the config
    config_data = _process_dict_env_vars(config_data or {})

    # Create and return the config instance
    _config_instance = JiminiConfig(**config_data)
    return _config_instance


def reload_config() -> JiminiConfig:
    """Force reload of the configuration"""
    global _config_instance
    _config_instance = None
    return get_config()
