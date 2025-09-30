# tests/test_config.py
import os
import tempfile
from app.config import load_config, Config

def test_load_config_from_yaml():
    """Test loading configuration from YAML file."""
    yaml_content = """
app:
  env: test
  shadow_mode: true
  shadow_overrides:
    - "RULE-1"
    - "RULE-2"

notifiers:
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/test"
    
siem:
  jsonl:
    enabled: true
    path: "logs/test.jsonl"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        config_path = f.name
    
    try:
        cfg = load_config(config_path)
        
        assert cfg.app.env == "test"
        assert cfg.app.shadow_mode is True
        assert "RULE-1" in cfg.app.shadow_overrides
        assert "RULE-2" in cfg.app.shadow_overrides
        assert cfg.notifiers.slack.enabled is True
        assert cfg.notifiers.slack.webhook_url == "https://hooks.slack.com/test"
        assert cfg.siem.jsonl.enabled is True
        assert cfg.siem.jsonl.path == "logs/test.jsonl"
    finally:
        os.unlink(config_path)

def test_load_config_with_env_vars():
    """Test loading configuration with environment variable expansion."""
    os.environ["TEST_WEBHOOK_URL"] = "https://hooks.slack.com/services/test123"
    
    yaml_content = """
notifiers:
  slack:
    enabled: true
    webhook_url: "${TEST_WEBHOOK_URL}"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        config_path = f.name
    
    try:
        cfg = load_config(config_path)
        
        assert cfg.notifiers.slack.webhook_url == "https://hooks.slack.com/services/test123"
    finally:
        os.unlink(config_path)
        del os.environ["TEST_WEBHOOK_URL"]

def test_load_config_defaults():
    """Test loading default configuration when file doesn't exist."""
    cfg = load_config("nonexistent_config.yaml")
    
    # Should return default config
    assert isinstance(cfg, Config)
    assert cfg.app.env == "dev"
    assert cfg.app.shadow_mode is False  # Unless JIMINI_SHADOW env is set

def test_shadow_override_empty():
    """Test that shadow_overrides defaults to empty list."""
    yaml_content = """
app:
  env: test
  shadow_mode: true
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        config_path = f.name
    
    try:
        cfg = load_config(config_path)
        
        assert cfg.app.shadow_overrides == []
    finally:
        os.unlink(config_path)
