import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app, apply_shadow_logic


@pytest.fixture
def test_client():
    return TestClient(app)


def test_apply_shadow_logic():
    # Test case 1: Not in shadow mode
    decision1, effective1 = apply_shadow_logic("BLOCK", ["RULE-1"], shadow_mode=False)
    assert decision1 == "BLOCK"
    assert effective1 == "BLOCK"  # Should enforce

    # Test case 2: In shadow mode with override
    decision2, effective2 = apply_shadow_logic(
        "BLOCK", ["OVERRIDE-RULE"], shadow_mode=True, shadow_overrides=["OVERRIDE-RULE"]
    )
    assert decision2 == "BLOCK"
    assert effective2 == "BLOCK"  # Should enforce despite shadow mode

    # Test case 3: In shadow mode without override
    decision3, effective3 = apply_shadow_logic(
        "BLOCK", ["RULE-2"], shadow_mode=True, shadow_overrides=["OVERRIDE-RULE"]
    )
    assert decision3 == "BLOCK"
    assert effective3 == "ALLOW"  # Should not enforce in shadow mode


@patch("app.main.evaluate")
@patch("app.main.cfg")
def test_shadow_override_blocks_when_rule_listed(mock_cfg, mock_evaluate, test_client):
    # Configure shadow mode with override
    mock_cfg.app.shadow_mode = True
    mock_cfg.app.shadow_overrides = ["SECRETS-EXFIL"]

    # Mock evaluation to return BLOCK with the override rule
    mock_evaluate.return_value = MagicMock(
        action="block", rule_ids=["SECRETS-EXFIL"], message="Blocked due to secrets"
    )

    # Make request
    response = test_client.post(
        "/v1/evaluate",
        json={
            "api_key": "changeme",
            "text": "API key: api_key=abcdefghijklmnop",
            "endpoint": "/test",
            "direction": "inbound",
        },
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "block"  # Should enforce the block due to override


@patch("app.main.evaluate")
@patch("app.main.cfg")
def test_shadow_allows_when_not_overridden(mock_cfg, mock_evaluate, test_client):
    # Configure shadow mode without override for the rule
    mock_cfg.app.shadow_mode = True
    mock_cfg.app.shadow_overrides = []

    # Mock evaluation to return BLOCK with a non-override rule
    mock_evaluate.return_value = MagicMock(
        action="block",
        rule_ids=["IL-AI-1.1"],
        message="Blocked due to sensitive content",
    )

    # Make request
    response = test_client.post(
        "/v1/evaluate",
        json={
            "api_key": "changeme",
            "text": "This contains sensitive content",
            "endpoint": "/test",
            "direction": "inbound",
        },
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "allow"  # Should allow in shadow mode
