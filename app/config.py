import os
import yaml
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("JIMINI_API_KEY", "changeme")
RULES_PATH = os.getenv("JIMINI_RULES_PATH", "policy_rules.yaml")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", None)

# Phase 3: Enhanced configuration with YAML support

@dataclass
class AppConfig:
    env: str = "dev"
    shadow_mode: bool = False
    shadow_overrides: List[str] = field(default_factory=list)

@dataclass
class SlackConfig:
    enabled: bool = False
    webhook_url: str = ""
    channel: str = "#jimini-alerts"
    username: str = "Jimini"
    icon_emoji: str = ":shield:"

@dataclass
class TeamsConfig:
    enabled: bool = False
    webhook_url: str = ""

@dataclass
class NotifiersConfig:
    slack: SlackConfig = field(default_factory=SlackConfig)
    teams: TeamsConfig = field(default_factory=TeamsConfig)

@dataclass
class JsonlSiemConfig:
    enabled: bool = False
    path: str = "logs/jimini_events.jsonl"

@dataclass
class SplunkHecConfig:
    enabled: bool = False
    url: str = ""
    token: str = ""
    sourcetype: str = "jimini:event"
    verify_tls: bool = True

@dataclass
class ElasticConfig:
    enabled: bool = False
    url: str = ""
    basic_auth_user: str = ""
    basic_auth_pass: str = ""
    verify_tls: bool = True

@dataclass
class SiemConfig:
    jsonl: JsonlSiemConfig = field(default_factory=JsonlSiemConfig)
    splunk_hec: SplunkHecConfig = field(default_factory=SplunkHecConfig)
    elastic: ElasticConfig = field(default_factory=ElasticConfig)

@dataclass
class OtelConfig:
    enabled: bool = False
    endpoint: str = ""
    service_name: str = "jimini"
    resource: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Config:
    app: AppConfig = field(default_factory=AppConfig)
    notifiers: NotifiersConfig = field(default_factory=NotifiersConfig)
    siem: SiemConfig = field(default_factory=SiemConfig)
    otel: OtelConfig = field(default_factory=OtelConfig)

_config_instance: Optional[Config] = None

def _expand_env_vars(obj: Any) -> Any:
    """Recursively expand ${VAR} placeholders in strings."""
    if isinstance(obj, str):
        # Replace ${VAR} with env var value
        import re
        pattern = r'\$\{([^}]+)\}'
        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))
        return re.sub(pattern, replacer, obj)
    elif isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_expand_env_vars(item) for item in obj]
    return obj

def _dict_to_dataclass(cls, data: Dict[str, Any]):
    """Convert a dict to a dataclass instance, handling nested dataclasses."""
    if not data:
        return cls()
    
    kwargs = {}
    for field_name, field_type in cls.__annotations__.items():
        if field_name not in data:
            continue
        
        value = data[field_name]
        
        # Check if field_type is a dataclass
        if hasattr(field_type, '__dataclass_fields__'):
            kwargs[field_name] = _dict_to_dataclass(field_type, value if isinstance(value, dict) else {})
        else:
            kwargs[field_name] = value
    
    return cls(**kwargs)

def load_config(config_path: str = "jimini.config.yaml") -> Config:
    """Load configuration from YAML file with env var expansion."""
    global _config_instance
    
    # If config file doesn't exist, return defaults
    if not os.path.exists(config_path):
        # Use environment variables and sensible defaults
        cfg = Config()
        
        # Shadow mode from env
        cfg.app.shadow_mode = os.getenv("JIMINI_SHADOW") == "1"
        
        # Enable JSONL by default if in shadow mode
        if cfg.app.shadow_mode:
            cfg.siem.jsonl.enabled = True
        
        # Slack notifier from legacy WEBHOOK_URL
        webhook_url = os.getenv("WEBHOOK_URL", "")
        if webhook_url:
            cfg.notifiers.slack.enabled = True
            cfg.notifiers.slack.webhook_url = webhook_url
        
        # OTEL from env
        otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        if otel_endpoint:
            cfg.otel.enabled = True
            cfg.otel.endpoint = otel_endpoint
        
        return cfg
    
    # Load from YAML
    with open(config_path, 'r') as f:
        raw_data = yaml.safe_load(f) or {}
    
    # Expand environment variables
    expanded_data = _expand_env_vars(raw_data)
    
    # Convert to Config dataclass
    cfg = Config()
    if 'app' in expanded_data:
        cfg.app = _dict_to_dataclass(AppConfig, expanded_data['app'])
    if 'notifiers' in expanded_data:
        notif_data = expanded_data['notifiers']
        cfg.notifiers = NotifiersConfig()
        if 'slack' in notif_data:
            cfg.notifiers.slack = _dict_to_dataclass(SlackConfig, notif_data['slack'])
        if 'teams' in notif_data:
            cfg.notifiers.teams = _dict_to_dataclass(TeamsConfig, notif_data['teams'])
    if 'siem' in expanded_data:
        siem_data = expanded_data['siem']
        cfg.siem = SiemConfig()
        if 'jsonl' in siem_data:
            cfg.siem.jsonl = _dict_to_dataclass(JsonlSiemConfig, siem_data['jsonl'])
        if 'splunk_hec' in siem_data:
            cfg.siem.splunk_hec = _dict_to_dataclass(SplunkHecConfig, siem_data['splunk_hec'])
        if 'elastic' in siem_data:
            cfg.siem.elastic = _dict_to_dataclass(ElasticConfig, siem_data['elastic'])
    if 'otel' in expanded_data:
        cfg.otel = _dict_to_dataclass(OtelConfig, expanded_data['otel'])
    
    return cfg

def get_config() -> Config:
    """Get or create the singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance
