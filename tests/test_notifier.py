# tests/test_notifier.py
import json
from unittest.mock import Mock, patch, MagicMock
from app.notifier import Notifier
from app.config import NotifiersConfig, SlackConfig, TeamsConfig
from app.telemetry import TelemetryEvent

def test_notifier_slack_enabled():
    """Test Notifier sends to Slack when enabled."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Create config with Slack enabled
        cfg = NotifiersConfig()
        cfg.slack = SlackConfig(
            enabled=True,
            webhook_url="https://hooks.slack.com/test"
        )
        
        notifier = Notifier(cfg)
        
        evt = TelemetryEvent(
            ts="2025-01-01T00:00:00Z",
            endpoint="/v1/evaluate",
            direction="outbound",
            decision="BLOCK",
            shadow_mode=False,
            rule_ids=["TEST-1.0", "TEST-2.0"],
            request_id="req_123",
            latency_ms=10.5
        )
        
        notifier.notify(evt)
        
        # Verify urlopen was called
        assert mock_urlopen.called
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        
        # Verify payload
        data = request.data.decode('utf-8')
        payload = json.loads(data)
        assert "text" in payload
        assert "BLOCK" in payload["text"]
        assert "TEST-1.0" in payload["text"]
        assert "req_123" in payload["text"]

def test_notifier_teams_enabled():
    """Test Notifier sends to Teams when enabled."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Create config with Teams enabled
        cfg = NotifiersConfig()
        cfg.teams = TeamsConfig(
            enabled=True,
            webhook_url="https://outlook.office.com/webhook/test"
        )
        
        notifier = Notifier(cfg)
        
        evt = TelemetryEvent(
            ts="2025-01-01T00:00:00Z",
            endpoint="/v1/evaluate",
            direction="outbound",
            decision="FLAG",
            shadow_mode=True,
            rule_ids=["TEST-3.0"],
            request_id="req_456",
            latency_ms=20.0
        )
        
        notifier.notify(evt)
        
        # Verify urlopen was called
        assert mock_urlopen.called
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        
        # Verify payload
        data = request.data.decode('utf-8')
        payload = json.loads(data)
        assert "text" in payload
        assert "FLAG" in payload["text"]
        assert "TEST-3.0" in payload["text"]

def test_notifier_disabled():
    """Test Notifier doesn't send when disabled."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        # Create config with both disabled
        cfg = NotifiersConfig()
        cfg.slack.enabled = False
        cfg.teams.enabled = False
        
        notifier = Notifier(cfg)
        
        evt = TelemetryEvent(
            ts="2025-01-01T00:00:00Z",
            endpoint="/v1/evaluate",
            direction="outbound",
            decision="BLOCK",
            shadow_mode=False,
            rule_ids=["TEST-1.0"],
        )
        
        notifier.notify(evt)
        
        # Verify urlopen was NOT called
        assert not mock_urlopen.called
