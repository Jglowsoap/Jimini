# config/loader.py
"""
Single source of truth configuration system for Jimini.
Merges YAML + .env with precedence, typed validation, fail-fast behavior.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, AnyHttpUrl, Field, ValidationError, validator
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class SlackConfig(BaseModel):
    """Slack notification configuration"""
    enabled: bool = False
    webhook_url: Optional[AnyHttpUrl] = None
    rate_limit_per_minute: int = Field(default=10, ge=1, le=100)
    
    @validator('webhook_url', always=True)
    def validate_webhook_if_enabled(cls, v, values):
        if values.get('enabled') and not v:
            raise ValueError("slack.webhook_url is required when slack.enabled=true")
        return v


class TeamsConfig(BaseModel):
    """Microsoft Teams notification configuration"""
    enabled: bool = False
    webhook_url: Optional[AnyHttpUrl] = None
    rate_limit_per_minute: int = Field(default=10, ge=1, le=100)
    
    @validator('webhook_url')
    def validate_webhook_if_enabled(cls, v, values):
        if values.get('enabled') and not v:
            raise ValueError("teams.webhook_url is required when teams.enabled=true")
        return v


class NotifiersConfig(BaseModel):
    """Notification services configuration"""
    slack: SlackConfig = SlackConfig()
    teams: TeamsConfig = TeamsConfig()


class SplunkConfig(BaseModel):
    """Splunk HEC forwarder configuration"""
    enabled: bool = False
    hec_url: Optional[AnyHttpUrl] = None
    hec_token: Optional[str] = None
    index: str = "main"
    verify_tls: bool = True
    
    @validator('hec_url')
    def validate_hec_url_if_enabled(cls, v, values):
        if values.get('enabled') and not v:
            raise ValueError("splunk.hec_url is required when splunk.enabled=true")
        return v
    
    @validator('hec_token')
    def validate_hec_token_if_enabled(cls, v, values):
        if values.get('enabled') and not v:
            raise ValueError("splunk.hec_token is required when splunk.enabled=true")
        return v


class ElasticConfig(BaseModel):
    """Elasticsearch forwarder configuration"""
    enabled: bool = False
    url: Optional[AnyHttpUrl] = None
    username: Optional[str] = None
    password: Optional[str] = None
    index: str = "jimini-events"
    verify_tls: bool = True
    
    @validator('url')
    def validate_url_if_enabled(cls, v, values):
        if values.get('enabled') and not v:
            raise ValueError("elastic.url is required when elastic.enabled=true")
        return v


class JsonlConfig(BaseModel):
    """JSONL file forwarder configuration"""
    enabled: bool = True
    file_path: str = "logs/jimini_events.jsonl"
    rotate_daily: bool = True
    retention_days: int = Field(default=30, ge=1, le=365)


class SiemConfig(BaseModel):
    """SIEM integration configuration"""
    jsonl: JsonlConfig = JsonlConfig()
    splunk: SplunkConfig = SplunkConfig()
    elastic: ElasticConfig = ElasticConfig()


class OtelConfig(BaseModel):
    """OpenTelemetry configuration"""
    enabled: bool = False
    endpoint: Optional[AnyHttpUrl] = None
    service_name: str = "jimini"
    
    @validator('endpoint')
    def validate_endpoint_if_enabled(cls, v, values):
        if values.get('enabled') and not v:
            raise ValueError("otel.endpoint is required when otel.enabled=true")
        return v


class AppConfig(BaseModel):
    """Core application configuration"""
    env: str = Field(default="dev", pattern="^(dev|staging|prod)$")
    shadow_mode: bool = True
    shadow_overrides: List[str] = []
    api_key: str = Field(default="changeme")
    host: str = "0.0.0.0"
    port: int = Field(default=9000, ge=1, le=65535)
    use_pii: bool = Field(default=False, description="Allow PII in outbound payloads")
    
    @validator('api_key')
    def validate_api_key_in_prod(cls, v, values):
        if values.get('env') == 'prod' and v == 'changeme':
            raise ValueError("api_key must be changed from default in production")
        return v


class SecurityConfig(BaseModel):
    """Security and compliance configuration"""
    rbac_enabled: bool = False
    admin_roles: List[str] = ["ADMIN"]
    reviewer_roles: List[str] = ["ADMIN", "REVIEWER"] 
    support_roles: List[str] = ["ADMIN", "REVIEWER", "SUPPORT"]


class Config(BaseModel):
    """Complete Jimini configuration"""
    app: AppConfig = AppConfig()
    notifiers: NotifiersConfig = NotifiersConfig()
    siem: SiemConfig = SiemConfig()
    otel: OtelConfig = OtelConfig()
    security: SecurityConfig = SecurityConfig()
    
    class Config:
        extra = "forbid"  # Disallow unknown keys
        
    @property
    def version(self) -> str:
        """Configuration version for health checks"""
        return "0.2.0"
    
    @property
    def profile(self) -> str:
        """Active configuration profile"""
        return self.app.env


def merge_env_vars(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Merge environment variables into config dict with precedence"""
    
    # Environment variable mappings
    env_mappings = {
        'JIMINI_API_KEY': 'app.api_key',
        'JIMINI_ENV': 'app.env', 
        'JIMINI_SHADOW_MODE': 'app.shadow_mode',
        'JIMINI_HOST': 'app.host',
        'JIMINI_PORT': 'app.port',
        'JIMINI_USE_PII': 'app.use_pii',
        
        'SLACK_WEBHOOK_URL': 'notifiers.slack.webhook_url',
        'TEAMS_WEBHOOK_URL': 'notifiers.teams.webhook_url',
        
        'SPLUNK_HEC_URL': 'siem.splunk.hec_url',
        'SPLUNK_HEC_TOKEN': 'siem.splunk.hec_token',
        'SPLUNK_INDEX': 'siem.splunk.index',
        'SPLUNK_VERIFY_TLS': 'siem.splunk.verify_tls',
        
        'ELASTIC_URL': 'siem.elastic.url',
        'ELASTIC_USERNAME': 'siem.elastic.username', 
        'ELASTIC_PASSWORD': 'siem.elastic.password',
        'ELASTIC_INDEX': 'siem.elastic.index',
        'ELASTIC_VERIFY_TLS': 'siem.elastic.verify_tls',
        
        'OTEL_EXPORTER_OTLP_ENDPOINT': 'otel.endpoint',
        'OTEL_SERVICE_NAME': 'otel.service_name',
        
        'JSONL_FILE_PATH': 'siem.jsonl.file_path',
        'JSONL_RETENTION_DAYS': 'siem.jsonl.retention_days',
    }
    
    def set_nested_key(d: Dict, key_path: str, value: Any):
        """Set nested dictionary key using dot notation"""
        keys = key_path.split('.')
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        
        # Type conversion for boolean/int values
        if isinstance(value, str):
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
        
        d[keys[-1]] = value
    
    # Apply environment variable overrides
    for env_var, config_path in env_mappings.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            set_nested_key(config_dict, config_path, env_value)
    
    return config_dict


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load and validate YAML configuration file"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        # Return default empty config if file doesn't exist
        return {}
    
    try:
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f) or {}
        return config_data
    except yaml.YAMLError as e:
        raise SystemExit(f"[config] YAML parse error in {config_path}: {e}")
    except Exception as e:
        raise SystemExit(f"[config] Failed to read {config_path}: {e}")


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML + environment variables with validation.
    Fails fast on missing required config when features are enabled.
    """
    
    # Default config path
    if config_path is None:
        config_path = os.getenv('JIMINI_CONFIG_PATH', 'jimini.config.yaml')
    
    try:
        # Load base YAML config
        config_dict = load_yaml_config(config_path)
        
        # Merge environment variable overrides
        config_dict = merge_env_vars(config_dict)
        
        # Enable features based on environment variables
        if os.getenv('SLACK_WEBHOOK_URL'):
            config_dict.setdefault('notifiers', {}).setdefault('slack', {})['enabled'] = True
        if os.getenv('TEAMS_WEBHOOK_URL'):
            config_dict.setdefault('notifiers', {}).setdefault('teams', {})['enabled'] = True
        if os.getenv('SPLUNK_HEC_URL'):
            config_dict.setdefault('siem', {}).setdefault('splunk', {})['enabled'] = True
        if os.getenv('ELASTIC_URL'):
            config_dict.setdefault('siem', {}).setdefault('elastic', {})['enabled'] = True
        if os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
            config_dict.setdefault('otel', {})['enabled'] = True
        
        # Create and validate config
        config = Config(**config_dict)
        
        return config
        
    except ValidationError as e:
        error_lines = []
        for error in e.errors():
            field = '.'.join(str(x) for x in error['loc'])
            msg = error['msg']
            error_lines.append(f"  {field}: {msg}")
        
        raise SystemExit(
            f"[config] Validation failed:\n" + '\n'.join(error_lines) + 
            f"\n\nConfig file: {config_path}"
        )
    except Exception as e:
        raise SystemExit(f"[config] Unexpected error loading config: {e}")


def mask_secrets(config: Config) -> Dict[str, Any]:
    """Return config dict with secrets masked for logging/health checks"""
    config_dict = config.dict()
    
    # Fields to mask
    secret_fields = [
        'api_key', 'hec_token', 'password', 'webhook_url'
    ]
    
    def mask_recursive(obj):
        if isinstance(obj, dict):
            return {
                key: '***MASKED***' if any(secret in key for secret in secret_fields) else mask_recursive(val)
                for key, val in obj.items()
            }
        elif isinstance(obj, list):
            return [mask_recursive(item) for item in obj]
        else:
            return obj
    
    return mask_recursive(config_dict)


# Global config instance (lazy loaded)
_config_instance: Optional[Config] = None


def get_current_config() -> Config:
    """Get the current global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = get_config()
    return _config_instance


def reload_config(config_path: Optional[str] = None) -> Config:
    """Reload configuration from file"""
    global _config_instance
    _config_instance = get_config(config_path)
    return _config_instance