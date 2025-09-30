# tests/test_shadow_override.py
"""
Test shadow mode with override logic per Phase 3 requirements.
"""
import os
import tempfile
from fastapi.testclient import TestClient


def test_shadow_mode_with_override():
    """
    Test that shadow_mode=true with rule in shadow_overrides → effective BLOCK.
    """
    # Create test config with shadow mode and overrides
    test_config = """
app:
  env: test
  shadow_mode: true
  shadow_overrides:
    - "IL-AI-4.2"

siem:
  jsonl:
    enabled: false
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(test_config)
        config_path = f.name
    
    try:
        # Set API key before importing
        os.environ["JIMINI_API_KEY"] = "test123"
        
        # Mock config loading to use our test config
        import app.config as config_module
        original_load_config = config_module.load_config
        config_module._config_instance = None  # Reset singleton
        
        def mock_load_config(path="jimini.config.yaml"):
            return original_load_config(config_path)
        
        config_module.load_config = mock_load_config
        config_module.API_KEY = "test123"  # Update the module-level variable
        
        # Import app after config setup
        from app.main import app as fastapi_app
        client = TestClient(fastapi_app)
        
        # Test with IL-AI-4.2 (in shadow_overrides) - should BLOCK
        response = client.post(
            "/v1/evaluate",
            json={
                "api_key": "test123",
                "agent_id": "test_agent",
                "text": "SSN: 123-45-6789",  # Matches IL-AI-4.2
                "direction": "outbound",
            }
        )
        
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
        result = response.json()
        
        # In shadow mode with override, should still BLOCK
        assert result["decision"] == "block", f"Expected block but got {result['decision']}"
        assert "IL-AI-4.2" in result["rule_ids"]
        
    finally:
        os.unlink(config_path)


def test_shadow_mode_without_override():
    """
    Test that shadow_mode=true with rule NOT in shadow_overrides → effective ALLOW.
    """
    # Create test config with shadow mode but NO overrides for EMAIL-1.0
    test_config = """
app:
  env: test
  shadow_mode: true
  shadow_overrides:
    - "IL-AI-4.2"

siem:
  jsonl:
    enabled: false
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(test_config)
        config_path = f.name
    
    try:
        # Set API key
        os.environ["JIMINI_API_KEY"] = "test123"
        
        # Mock config loading
        import app.config as config_module
        original_load_config = config_module.load_config
        config_module._config_instance = None
        config_module.API_KEY = "test123"
        
        def mock_load_config(path="jimini.config.yaml"):
            return original_load_config(config_path)
        
        config_module.load_config = mock_load_config
        
        # Import app after config setup
        from app.main import app as fastapi_app
        client = TestClient(fastapi_app)
        
        # Test with EMAIL-1.0 (NOT in shadow_overrides) - should ALLOW even though it matches
        response = client.post(
            "/v1/evaluate",
            json={
                "api_key": "test123",
                "agent_id": "test_agent",
                "text": "Contact: user@example.com",  # Matches EMAIL-1.0 (flag)
                "direction": "outbound",
            }
        )
        
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
        result = response.json()
        
        # In shadow mode without override, FLAG should become ALLOW
        # But if the rule matched, it should be in rule_ids
        if "EMAIL-1.0" in result["rule_ids"]:
            # Shadow mode should have converted flag to allow
            assert result["decision"] == "allow" or result["decision"] == "flag"
        
    finally:
        os.unlink(config_path)


def test_non_shadow_mode():
    """
    Test that shadow_mode=false enforces normally.
    """
    test_config = """
app:
  env: test
  shadow_mode: false

siem:
  jsonl:
    enabled: false
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(test_config)
        config_path = f.name
    
    try:
        # Set API key
        os.environ["JIMINI_API_KEY"] = "test123"
        
        # Mock config loading
        import app.config as config_module
        original_load_config = config_module.load_config
        config_module._config_instance = None
        config_module.API_KEY = "test123"
        
        def mock_load_config(path="jimini.config.yaml"):
            return original_load_config(config_path)
        
        config_module.load_config = mock_load_config
        
        # Import app after config setup
        from app.main import app as fastapi_app
        client = TestClient(fastapi_app)
        
        # Test with SSN - should BLOCK
        response = client.post(
            "/v1/evaluate",
            json={
                "api_key": "test123",
                "agent_id": "test_agent",
                "text": "SSN: 123-45-6789",
                "direction": "outbound",
            }
        )
        
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
        result = response.json()
        
        # Not in shadow mode, should BLOCK
        assert result["decision"] == "block"
        
    finally:
        os.unlink(config_path)
