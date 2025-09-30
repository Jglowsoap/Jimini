import json
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_config(tmp_path):
    # Create a mock configuration with a temporary JSONL path
    config = MagicMock()
    config.app.shadow_mode = False
    config.siem.jsonl.enabled = True
    config.siem.jsonl.path = str(tmp_path / "events.jsonl")
    config.siem.splunk_hec.enabled = False
    config.siem.elastic.enabled = False
    config.notifiers.slack.enabled = False
    config.notifiers.teams.enabled = False
    return config


@patch("app.main.evaluate")
@patch("app.main.cfg")
def test_evaluate_writes_jsonl(
    mock_cfg, mock_evaluate, test_client, mock_config, tmp_path
):
    # Set up mocks
    mock_cfg.configure_mock(
        **{
            "app.shadow_mode": False,
            "siem.jsonl.enabled": True,
            "siem.jsonl.path": str(tmp_path / "events.jsonl"),
        }
    )

    # Mock evaluate to return ALLOW
    mock_evaluate.return_value = MagicMock(action="allow", rule_ids=[], message="")

    # Make request
    response = test_client.post(
        "/v1/evaluate",
        json={
            "api_key": "changeme",
            "text": "Hello world",
            "endpoint": "/test",
            "direction": "inbound",
        },
    )

    assert response.status_code == 200

    # Check JSONL file
    jsonl_path = tmp_path / "events.jsonl"
    assert os.path.exists(jsonl_path)

    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) >= 1

    # Parse and check all events
    events = [json.loads(line) for line in lines]

    # Should have at least one inbound and one outbound event
    inbound = [e for e in events if e["direction"] == "inbound"]
    outbound = [e for e in events if e["direction"] == "outbound"]

    assert len(inbound) > 0
    assert len(outbound) > 0


@patch("app.main.evaluate")
@patch("app.main.cfg")
def test_shadow_mode_behavior(mock_cfg, mock_evaluate, test_client):
    # Set shadow mode on
    mock_cfg.app.shadow_mode = True
    mock_cfg.app.shadow_overrides = ["SECRETS-EXFIL"]

    # Test case 1: Rule that should be enforced even in shadow mode
    mock_evaluate.return_value = MagicMock(
        action="block", rule_ids=["SECRETS-EXFIL"], message="Blocked due to secrets"
    )

    response1 = test_client.post(
        "/v1/evaluate",
        json={
            "api_key": "changeme",
            "text": "API key: api_key=abcdefghijklmnop",
            "endpoint": "/test",
            "direction": "inbound",
        },
    )

    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["action"] == "block"  # Should be blocked despite shadow mode

    # Test case 2: Rule that should NOT be enforced in shadow mode
    mock_evaluate.return_value = MagicMock(
        action="block",
        rule_ids=["IL-AI-1.1"],
        message="Blocked due to sensitive content",
    )

    response2 = test_client.post(
        "/v1/evaluate",
        json={
            "api_key": "changeme",
            "text": "This contains sensitive content",
            "endpoint": "/test",
            "direction": "inbound",
        },
    )

    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["action"] == "allow"  # Should be allowed in shadow mode
