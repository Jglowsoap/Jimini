import json
from unittest.mock import patch, MagicMock
from app.notifier import Notifier
from app.telemetry import TelemetryEvent


class DummyResp:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_slack_notified_on_block(monkeypatch):
    sent = {}

    def fake_urlopen(req, timeout=5, context=None):
        sent["url"] = req.full_url
        sent["data"] = json.loads(req.data.decode())
        return DummyResp()

    with patch("urllib.request.urlopen", fake_urlopen):
        # Create mock config
        mock_slack = MagicMock()
        mock_slack.enabled = True
        mock_slack.webhook_url = "https://hooks.slack.com/services/abc"

        mock_teams = MagicMock()
        mock_teams.enabled = False
        mock_teams.webhook_url = None

        mock_config = MagicMock()
        mock_config.slack = mock_slack
        mock_config.teams = mock_teams

        # Create notifier and event
        notifier = Notifier(mock_config)
        event = TelemetryEvent(
            ts="2023-01-01T12:00:00.000Z",
            endpoint="/v1/evaluate",
            direction="outbound",
            decision="BLOCK",
            shadow_mode=True,
            rule_ids=["SECRETS-EXFIL"],
            request_id="req1",
            latency_ms=12.3,
        )

        # Notify
        notifier.notify(event)

        # Assertions
        assert "hooks.slack.com" in sent["url"]
        assert "Jimini Alert" in sent["data"]["text"]
        assert "BLOCK" in sent["data"]["text"]
        assert "SECRETS-EXFIL" in sent["data"]["text"]
        assert "req1" in sent["data"]["text"]


def test_teams_notification(monkeypatch):
    sent = {}

    def fake_urlopen(req, timeout=5, context=None):
        sent["url"] = req.full_url
        sent["data"] = json.loads(req.data.decode())
        return DummyResp()

    with patch("urllib.request.urlopen", fake_urlopen):
        # Create mock config
        mock_slack = MagicMock()
        mock_slack.enabled = False

        mock_teams = MagicMock()
        mock_teams.enabled = True
        mock_teams.webhook_url = "https://teams-webhook.example.com/webhook"

        mock_config = MagicMock()
        mock_config.slack = mock_slack
        mock_config.teams = mock_teams

        # Create notifier and event
        notifier = Notifier(mock_config)
        event = TelemetryEvent(
            ts="2023-01-01T12:00:00.000Z",
            endpoint="/v1/evaluate",
            direction="outbound",
            decision="FLAG",
            shadow_mode=False,
            rule_ids=["IL-AI-1.1"],
            request_id="req2",
            latency_ms=15.7,
        )

        # Notify
        notifier.notify(event)

        # Assertions
        assert "teams-webhook.example.com" in sent["url"]
        assert "text" in sent["data"]
        assert "FLAG" in sent["data"]["text"]
        assert "IL-AI-1.1" in sent["data"]["text"]
