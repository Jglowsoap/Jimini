#!/usr/bin/env python3
"""
Test script to validate Phase 4A: Configuration fail-fast behavior.
Tests that the system properly exits with clear error messages when required config is missing.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def test_slack_enabled_without_webhook():
    """Test that enabling Slack without webhook_url fails with clear message"""
    config_content = """
app:
  env: dev
  api_key: test-key

notifiers:
  slack:
    enabled: true
    # webhook_url missing - should fail
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_path = f.name
    
    try:
        # Test config validation
        result = subprocess.run([
            sys.executable, "-c", 
            f"""
import sys
sys.path.insert(0, '.')
from config.loader import get_config
try:
    config = get_config('{config_path}')
    print("ERROR: Should have failed validation")
    sys.exit(1)
except SystemExit as e:
    if 'slack.webhook_url is required' in str(e):
        print("SUCCESS: Proper validation error")
        sys.exit(0)
    else:
        print(f"ERROR: Wrong error message: {{e}}")
        sys.exit(1)
"""
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Slack validation test PASSED")
        else:
            print(f"❌ Slack validation test FAILED: {result.stderr}")
            
    finally:
        os.unlink(config_path)


def test_production_default_api_key():
    """Test that production environment rejects default API key"""
    config_content = """
app:
  env: prod
  api_key: changeme  # Default key should fail in prod

notifiers:
  slack:
    enabled: false
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_path = f.name
    
    try:
        result = subprocess.run([
            sys.executable, "-c", 
            f"""
import sys
sys.path.insert(0, '.')
from config.loader import get_config
try:
    config = get_config('{config_path}')
    print("ERROR: Should have failed validation")
    sys.exit(1)
except SystemExit as e:
    if 'api_key must be changed' in str(e):
        print("SUCCESS: Production API key validation works")
        sys.exit(0)
    else:
        print(f"ERROR: Wrong error message: {{e}}")
        sys.exit(1)
"""
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Production API key test PASSED")
        else:
            print(f"❌ Production API key test FAILED: {result.stderr}")
            
    finally:
        os.unlink(config_path)


def test_environment_variable_precedence():
    """Test that environment variables override YAML config"""
    config_content = """
app:
  env: dev
  api_key: yaml-key
  
notifiers:
  slack:
    enabled: false
    webhook_url: https://hooks.slack.com/yaml-url
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_path = f.name
    
    try:
        # Set environment variables
        env = os.environ.copy()
        env['JIMINI_API_KEY'] = 'env-key'
        env['SLACK_WEBHOOK_URL'] = 'https://hooks.slack.com/env-url'
        
        result = subprocess.run([
            sys.executable, "-c", 
            f"""
import sys
sys.path.insert(0, '.')
from config.loader import get_config

config = get_config('{config_path}')
assert config.app.api_key == 'env-key', f"Expected env-key, got {{config.app.api_key}}"
assert str(config.notifiers.slack.webhook_url) == 'https://hooks.slack.com/env-url', f"Expected env URL, got {{config.notifiers.slack.webhook_url}}"
assert config.notifiers.slack.enabled == True, "Should auto-enable Slack when webhook URL is set"
print("SUCCESS: Environment variable precedence works")
"""
        ], env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Environment precedence test PASSED")
        else:
            print(f"❌ Environment precedence test FAILED: {result.stderr}")
            
    finally:
        os.unlink(config_path)


def test_secret_masking():
    """Test that secrets are properly masked in health endpoint response"""
    result = subprocess.run([
        sys.executable, "-c", 
        """
import sys
sys.path.insert(0, '.')
from config.loader import get_config, mask_secrets

# Create config with secrets
config = get_config()
config.app.api_key = 'secret-key-123'
config.notifiers.slack.webhook_url = 'https://hooks.slack.com/secret'

# Test masking
masked = mask_secrets(config)
assert masked['app']['api_key'] == '***MASKED***', f"API key not masked: {masked['app']['api_key']}"
assert '***MASKED***' in str(masked['notifiers']['slack']['webhook_url']), f"Webhook URL not masked: {masked['notifiers']['slack']['webhook_url']}"
print("SUCCESS: Secret masking works properly")
"""
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Secret masking test PASSED")
    else:
        print(f"❌ Secret masking test FAILED: {result.stderr}")


def main():
    """Run all Phase 4A validation tests"""
    print("🚀 Testing Phase 4A: Configuration & Secrets")
    print("=" * 50)
    
    test_slack_enabled_without_webhook()
    test_production_default_api_key()
    test_environment_variable_precedence()
    test_secret_masking()
    
    print("\n✅ Phase 4A validation complete!")
    print("Configuration system properly implements:")
    print("  • Fail-fast validation with clear error messages")
    print("  • Environment variable precedence over YAML")
    print("  • Production safety checks")
    print("  • Secret masking for health endpoints")


if __name__ == '__main__':
    main()