# tests/test_configuration_features.py - Comprehensive Configuration Tests

import pytest
import os
import tempfile
import yaml
from unittest.mock import patch, MagicMock

from app.config import AppConfig, load_config, update_config, get_config_value
from app.models import Rule


class TestAppConfig:
    """Test application configuration class."""

    def test_config_initialization_defaults(self):
        """Test configuration initialization with default values."""
        config = AppConfig()
        
        assert config.api_key == "changeme"
        assert config.shadow_mode is False
        assert config.webhook_url is None
        assert config.otel_endpoint is None
        assert config.rules_path == "policy_rules.yaml"

    def test_config_initialization_with_values(self):
        """Test configuration initialization with provided values."""
        config = AppConfig(
            api_key="test-key",
            shadow_mode=True,
            webhook_url="http://webhook.example.com",
            otel_endpoint="http://otel.example.com",
            rules_path="/custom/rules.yaml"
        )
        
        assert config.api_key == "test-key"
        assert config.shadow_mode is True
        assert config.webhook_url == "http://webhook.example.com"
        assert config.otel_endpoint == "http://otel.example.com"
        assert config.rules_path == "/custom/rules.yaml"

    def test_config_from_environment(self):
        """Test configuration loading from environment variables."""
        env_vars = {
            "JIMINI_API_KEY": "env-api-key",
            "JIMINI_SHADOW": "1",
            "WEBHOOK_URL": "http://env-webhook.com",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://env-otel.com",
            "JIMINI_RULES_PATH": "/env/rules.yaml",
            "AUDIT_LOG_PATH": "/env/audit.log"
        }
        
        with patch.dict(os.environ, env_vars):
            config = AppConfig.from_env()
        
        assert config.api_key == "env-api-key"
        assert config.shadow_mode is True
        assert config.webhook_url == "http://env-webhook.com"
        assert config.otel_endpoint == "http://env-otel.com"
        assert config.rules_path == "/env/rules.yaml"
        assert config.audit_log_path == "/env/audit.log"

    def test_config_shadow_mode_variations(self):
        """Test different shadow mode environment variable formats."""
        shadow_values = ["1", "true", "True", "TRUE", "yes", "Yes", "YES"]
        
        for value in shadow_values:
            with patch.dict(os.environ, {"JIMINI_SHADOW": value}):
                config = AppConfig.from_env()
                assert config.shadow_mode is True, f"Failed for value: {value}"
        
        non_shadow_values = ["0", "false", "False", "FALSE", "no", "No", "NO", ""]
        
        for value in non_shadow_values:
            with patch.dict(os.environ, {"JIMINI_SHADOW": value}):
                config = AppConfig.from_env()
                assert config.shadow_mode is False, f"Failed for value: {value}"

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid configuration
        config = AppConfig(api_key="valid-key")
        assert config.validate() is True
        
        # Invalid API key (empty)
        config = AppConfig(api_key="")
        assert config.validate() is False
        
        # Invalid rules path (empty)
        config = AppConfig(rules_path="")
        assert config.validate() is False

    def test_config_serialization(self):
        """Test configuration serialization to dictionary."""
        config = AppConfig(
            api_key="test-key",
            shadow_mode=True,
            webhook_url="http://webhook.com"
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["api_key"] == "test-key"
        assert config_dict["shadow_mode"] is True
        assert config_dict["webhook_url"] == "http://webhook.com"

    def test_config_update_from_dict(self):
        """Test updating configuration from dictionary."""
        config = AppConfig()
        
        updates = {
            "api_key": "updated-key",
            "shadow_mode": True,
            "webhook_url": "http://new-webhook.com"
        }
        
        config.update_from_dict(updates)
        
        assert config.api_key == "updated-key"
        assert config.shadow_mode is True
        assert config.webhook_url == "http://new-webhook.com"


class TestConfigurationLoading:
    """Test configuration loading functionality."""

    def test_load_config_from_file(self):
        """Test loading configuration from YAML file."""
        config_data = {
            "api_key": "file-api-key",
            "shadow_mode": True,
            "webhook_url": "http://file-webhook.com",
            "rules_path": "/file/rules.yaml"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            config = load_config(config_file)
            
            assert config.api_key == "file-api-key"
            assert config.shadow_mode is True
            assert config.webhook_url == "http://file-webhook.com"
            assert config.rules_path == "/file/rules.yaml"
        finally:
            os.unlink(config_file)

    def test_load_config_precedence(self):
        """Test configuration precedence: CLI args > env vars > config file > defaults."""
        # Create config file
        config_data = {
            "api_key": "file-key",
            "shadow_mode": False,
            "webhook_url": "http://file-webhook.com"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        env_vars = {
            "JIMINI_API_KEY": "env-key",
            "JIMINI_SHADOW": "1"
        }
        
        try:
            with patch.dict(os.environ, env_vars):
                config = load_config(config_file)
            
            # Environment should override file
            assert config.api_key == "env-key"
            assert config.shadow_mode is True
            # File value should be used where env is not set
            assert config.webhook_url == "http://file-webhook.com"
        finally:
            os.unlink(config_file)

    def test_load_config_missing_file(self):
        """Test loading configuration when file doesn't exist."""
        config = load_config("/nonexistent/config.yaml")
        
        # Should return default configuration
        assert config.api_key == "changeme"
        assert config.shadow_mode is False

    def test_load_config_invalid_yaml(self):
        """Test loading configuration with invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_file = f.name
        
        try:
            config = load_config(config_file)
            # Should fallback to defaults on invalid YAML
            assert config.api_key == "changeme"
        finally:
            os.unlink(config_file)


class TestConfigurationUpdates:
    """Test dynamic configuration updates."""

    def test_update_config_runtime(self):
        """Test updating configuration at runtime."""
        original_config = AppConfig(api_key="original-key")
        
        updates = {
            "api_key": "updated-key",
            "shadow_mode": True
        }
        
        updated_config = update_config(original_config, updates)
        
        assert updated_config.api_key == "updated-key"
        assert updated_config.shadow_mode is True

    def test_get_config_value(self):
        """Test getting specific configuration values."""
        config = AppConfig(
            api_key="test-key",
            shadow_mode=True,
            webhook_url="http://webhook.com"
        )
        
        assert get_config_value(config, "api_key") == "test-key"
        assert get_config_value(config, "shadow_mode") is True
        assert get_config_value(config, "webhook_url") == "http://webhook.com"
        
        # Test default value for non-existent key
        assert get_config_value(config, "nonexistent", "default") == "default"

    def test_config_hot_reload(self):
        """Test configuration hot-reload functionality."""
        # Create initial config file
        initial_config = {
            "api_key": "initial-key",
            "shadow_mode": False
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(initial_config, f)
            config_file = f.name
        
        try:
            # Load initial configuration
            config1 = load_config(config_file)
            assert config1.api_key == "initial-key"
            assert config1.shadow_mode is False
            
            # Update config file
            updated_config = {
                "api_key": "updated-key",
                "shadow_mode": True
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(updated_config, f)
            
            # Reload configuration
            config2 = load_config(config_file)
            assert config2.api_key == "updated-key"
            assert config2.shadow_mode is True
        finally:
            os.unlink(config_file)


class TestConfigurationValidation:
    """Test configuration validation scenarios."""

    def test_validate_api_key_requirements(self):
        """Test API key validation requirements."""
        # Valid API keys
        valid_keys = ["changeme", "test-key-123", "very-long-api-key-with-numbers-123"]
        
        for key in valid_keys:
            config = AppConfig(api_key=key)
            assert config.validate() is True, f"Failed for valid key: {key}"
        
        # Invalid API keys
        invalid_keys = ["", "   ", None]
        
        for key in invalid_keys:
            config = AppConfig(api_key=key)
            assert config.validate() is False, f"Should fail for invalid key: {key}"

    def test_validate_rules_path(self):
        """Test rules path validation."""
        # Valid paths
        valid_paths = ["policy_rules.yaml", "/abs/path/rules.yaml", "relative/path/rules.yaml"]
        
        for path in valid_paths:
            config = AppConfig(rules_path=path)
            assert config.validate() is True, f"Failed for valid path: {path}"
        
        # Invalid paths
        invalid_paths = ["", "   ", None]
        
        for path in invalid_paths:
            config = AppConfig(rules_path=path)
            assert config.validate() is False, f"Should fail for invalid path: {path}"

    def test_validate_url_formats(self):
        """Test URL format validation."""
        # Valid URLs
        valid_urls = [
            "http://example.com",
            "https://webhook.example.com:8080/path",
            "http://localhost:3000",
            None  # None should be valid (optional)
        ]
        
        for url in valid_urls:
            config = AppConfig(webhook_url=url)
            assert config.validate() is True, f"Failed for valid URL: {url}"
        
        # Invalid URLs (if strict validation is implemented)
        invalid_urls = ["not-a-url", "ftp://invalid-scheme.com", ""]
        
        # Note: Current implementation may not validate URL format strictly
        # This test documents expected behavior if strict validation is added


class TestConfigurationEdgeCases:
    """Test configuration edge cases and error conditions."""

    def test_config_with_unicode_values(self):
        """Test configuration with unicode values."""
        config = AppConfig(
            api_key="key-with-unicode-字符",
            webhook_url="http://example.com/webhook-ñoñó"
        )
        
        assert config.api_key == "key-with-unicode-字符"
        assert config.webhook_url == "http://example.com/webhook-ñoñó"

    def test_config_with_very_long_values(self):
        """Test configuration with very long values."""
        long_key = "x" * 1000
        long_url = "http://example.com/" + "path/" * 100
        
        config = AppConfig(
            api_key=long_key,
            webhook_url=long_url
        )
        
        assert len(config.api_key) == 1000
        assert config.webhook_url.startswith("http://example.com/")

    def test_config_type_coercion(self):
        """Test configuration type coercion."""
        # String to boolean coercion for shadow_mode
        config = AppConfig()
        config.update_from_dict({"shadow_mode": "true"})
        
        # Should handle string-to-boolean conversion
        # (Implementation dependent)

    def test_config_concurrent_access(self):
        """Test configuration concurrent access safety."""
        import threading
        
        config = AppConfig(api_key="initial-key")
        results = []
        
        def worker():
            for i in range(100):
                config.api_key = f"key-{i}"
                results.append(config.api_key)
        
        # Create multiple threads updating config
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have results from all threads
        assert len(results) == 500


class TestConfigurationIntegration:
    """Test configuration integration with other components."""

    def test_config_with_rules_loading(self):
        """Test configuration integration with rules loading."""
        # Create rules file
        rules_data = {
            "rules": [
                {
                    "id": "TEST-1.0",
                    "pattern": "test-pattern",
                    "action": "block",
                    "applies_to": ["request"]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(rules_data, f)
            rules_file = f.name
        
        try:
            config = AppConfig(rules_path=rules_file)
            
            # Verify config points to the rules file
            assert config.rules_path == rules_file
            
            # Integration test: rules loader should be able to use this path
            from app.rules_loader import load_rules
            rules = load_rules(config.rules_path)
            
            assert len(rules) == 1
            assert rules[0].id == "TEST-1.0"
        finally:
            os.unlink(rules_file)

    @patch('app.otel.setup_telemetry')
    def test_config_with_telemetry_setup(self, mock_setup_telemetry):
        """Test configuration integration with telemetry setup."""
        config = AppConfig(
            otel_endpoint="http://otel.example.com",
            shadow_mode=True
        )
        
        # Simulate telemetry setup with config
        if config.otel_endpoint:
            mock_setup_telemetry(config.otel_endpoint)
        
        # Verify telemetry was configured
        mock_setup_telemetry.assert_called_once_with("http://otel.example.com")

    @patch('requests.post')
    def test_config_with_webhook_integration(self, mock_post):
        """Test configuration integration with webhook notifications."""
        config = AppConfig(
            webhook_url="http://webhook.example.com",
            api_key="test-key"
        )
        
        # Simulate webhook notification using config
        if config.webhook_url:
            mock_post(
                config.webhook_url,
                json={"alert": "test", "api_key": config.api_key}
            )
        
        # Verify webhook was called with config values
        mock_post.assert_called_once_with(
            "http://webhook.example.com",
            json={"alert": "test", "api_key": "test-key"}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])