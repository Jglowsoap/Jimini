import unittest
from unittest.mock import patch, MagicMock
import json
import os
import tempfile

from app.telemetry import Telemetry, TelemetryEvent
from app.forwarders.jsonl_forwarder import JsonlForwarder
from app.notifier import Notifier


class TestTelemetryCounters(unittest.TestCase):
    def setUp(self):
        # Reset the singleton
        Telemetry._instance = None

    @patch("app.telemetry.get_config")
    def test_counters_update(self, mock_get_config):
        # Mock config to avoid loading from file
        mock_config = MagicMock()
        mock_config.siem.jsonl.enabled = False
        mock_config.notifiers.slack.enabled = False
        mock_config.notifiers.teams.enabled = False
        mock_get_config.return_value = mock_config

        telemetry = Telemetry()

        # Record events with different rule IDs
        telemetry.record_event(
            TelemetryEvent(
                ts="2023-01-01T00:00:00.000Z",
                endpoint="/v1/evaluate",
                direction="outbound",
                decision="BLOCK",
                shadow_mode=False,
                rule_ids=["RULE-1", "RULE-2"],
            )
        )

        telemetry.record_event(
            TelemetryEvent(
                ts="2023-01-01T00:00:01.000Z",
                endpoint="/v1/evaluate",
                direction="outbound",
                decision="FLAG",
                shadow_mode=False,
                rule_ids=["RULE-2"],
            )
        )

        # Check counters
        counters = telemetry.snapshot_counters()

        self.assertEqual(counters["/v1/evaluate|outbound|RULE-1|BLOCK"], 1)
        self.assertEqual(counters["/v1/evaluate|outbound|RULE-2|BLOCK"], 1)
        self.assertEqual(counters["/v1/evaluate|outbound|RULE-2|FLAG"], 1)


class TestJsonlForwarder(unittest.TestCase):
    def test_send_many(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.jsonl")
            forwarder = JsonlForwarder(log_path)

            events = [
                {
                    "ts": "2023-01-01T00:00:00.000Z",
                    "endpoint": "/test",
                    "rule_ids": ["RULE-1"],
                },
                {
                    "ts": "2023-01-01T00:00:01.000Z",
                    "endpoint": "/test",
                    "rule_ids": ["RULE-2"],
                },
            ]

            forwarder.send_many(events)

            # Check file content
            with open(log_path, "r") as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 2)
                self.assertEqual(json.loads(lines[0])["rule_ids"], ["RULE-1"])
                self.assertEqual(json.loads(lines[1])["rule_ids"], ["RULE-2"])


class TestNotifier(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_slack_notification(self, mock_urlopen):
        # Mock response
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Create notifier with mock config
        mock_config = MagicMock()
        mock_config.slack.enabled = True
        mock_config.slack.webhook_url = "https://hooks.slack.com/services/test"
        mock_config.teams.enabled = False

        notifier = Notifier(mock_config)

        # Create test event
        event = TelemetryEvent(
            ts="2023-01-01T00:00:00.000Z",
            endpoint="/v1/evaluate",
            direction="outbound",
            decision="BLOCK",
            shadow_mode=False,
            rule_ids=["RULE-1"],
            request_id="req_123",
            latency_ms=10.5,
        )

        # Notify
        notifier.notify(event)

        # Check call
        mock_urlopen.assert_called_once()
        args, kwargs = mock_urlopen.call_args
        self.assertEqual(kwargs["timeout"], 5)

        # Check request data
        request = args[0]
        self.assertEqual(request.get_header("Content-Type"), "application/json")

        # Check payload
        payload = json.loads(request.data.decode("utf-8"))
        self.assertIn("BLOCK", payload["text"])
        self.assertIn("RULE-1", payload["text"])
        self.assertIn("req_123", payload["text"])


class TestShadowOverride(unittest.TestCase):
    def setUp(self):
        # Reset the singleton
        Telemetry._instance = None

    @patch("app.telemetry.get_config")
    def test_shadow_override(self, mock_get_config):
        # Mock config with shadow mode enabled and overrides
        mock_config = MagicMock()
        mock_config.app.shadow_mode = True
        mock_config.app.shadow_overrides = ["RULE-1"]
        mock_config.siem.jsonl.enabled = False
        mock_config.notifiers.slack.enabled = False
        mock_config.notifiers.teams.enabled = False
        mock_get_config.return_value = mock_config

        from app.main import apply_shadow_logic

        # Test with rule in shadow_overrides
        decision, effective_decision = apply_shadow_logic("BLOCK", ["RULE-1"])
        self.assertEqual(effective_decision, "BLOCK")  # Should enforce

        # Test with rule not in shadow_overrides
        decision, effective_decision = apply_shadow_logic("BLOCK", ["RULE-2"])
        self.assertEqual(effective_decision, "ALLOW")  # Should not enforce
