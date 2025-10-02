"""Test configuration validation"""

import pytest
import tempfile
import os
from config.loader import get_config


def test_config_validation_slack_enabled_no_webhook():
    """Test that config fails when slack is enabled but no webhook URL provided"""
    
    test_config_content = """
app:
  env: dev
notifiers:
  slack:
    enabled: true
    # webhook_url not provided
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(test_config_content)
        config_path = f.name
    
    try:
        with pytest.raises(SystemExit):
            get_config(config_path)
    finally:
        os.unlink(config_path)


def test_config_validation_valid():
    """Test that valid config loads successfully"""
    
    test_config_content = """
app:
  env: dev
  api_key: test-key
notifiers:
  slack:
    enabled: false
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(test_config_content)
        config_path = f.name
    
    try:
        config = get_config(config_path)
        assert config.app.env == "dev"
        assert config.app.api_key == "test-key"
        assert not config.notifiers.slack.enabled
    finally:
        os.unlink(config_path)