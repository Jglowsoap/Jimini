import pytest
from unittest.mock import patch, MagicMock
from app.telemetry import Telemetry, TelemetryEvent


@pytest.fixture
def mock_telemetry():
    # Reset the singleton instance
    Telemetry._instance = None

    # Mock config and dependencies
    mock_config = MagicMock()
    mock_config.siem.jsonl.enabled = False
    mock_config.siem.splunk_hec.enabled = False
    mock_config.siem.elastic.enabled = False
    mock_config.notifiers.slack.enabled = False
    mock_config.notifiers.teams.enabled = False

    with patch("app.telemetry.get_config", return_value=mock_config):
        telemetry = Telemetry(flush_sec=0.1)  # Use short flush interval for tests

        # Add a reset helper method for tests
        def reset_for_tests():
            with telemetry.lock:
                telemetry.events.clear()
                telemetry.counters.clear()

        telemetry.reset_for_tests = reset_for_tests
        telemetry.reset_for_tests()

        yield telemetry

        # Clean up
        telemetry.stop()


def test_counters_increment_and_notify(mock_telemetry):
    # Replace notifier with a mock
    notified = {"count": 0}
    mock_telemetry.notifier.notify = lambda evt: notified.__setitem__(
        "count", notified["count"] + 1
    )

    # Record BLOCK event
    evt = TelemetryEvent(
        ts="2025-01-01T00:00:00Z",
        endpoint="/v1/evaluate",
        direction="outbound",
        decision="BLOCK",
        shadow_mode=True,
        rule_ids=["SECRETS-EXFIL"],
        request_id="r1",
    )
    mock_telemetry.record_event(evt)

    # Check counters and notifications
    snap = mock_telemetry.snapshot_counters()
    key = "/v1/evaluate|outbound|SECRETS-EXFIL|BLOCK"
    assert snap[key] == 1
    assert notified["count"] == 1

    # Record another event with same rule but different decision
    evt2 = TelemetryEvent(
        ts="2025-01-01T00:00:01Z",
        endpoint="/v1/evaluate",
        direction="outbound",
        decision="FLAG",
        shadow_mode=True,
        rule_ids=["SECRETS-EXFIL"],
        request_id="r2",
    )
    mock_telemetry.record_event(evt2)

    # Check updated counters and notifications
    snap = mock_telemetry.snapshot_counters()
    key1 = "/v1/evaluate|outbound|SECRETS-EXFIL|BLOCK"
    key2 = "/v1/evaluate|outbound|SECRETS-EXFIL|FLAG"
    assert snap[key1] == 1
    assert snap[key2] == 1
    assert notified["count"] == 2  # Both BLOCK and FLAG should notify


def test_counters_multiple_rules(mock_telemetry):
    # Record event with multiple rules
    evt = TelemetryEvent(
        ts="2025-01-01T00:00:00Z",
        endpoint="/v1/evaluate",
        direction="outbound",
        decision="BLOCK",
        shadow_mode=False,
        rule_ids=["RULE-1", "RULE-2"],
        request_id="r3",
    )
    mock_telemetry.record_event(evt)

    # Check counters for both rules
    snap = mock_telemetry.snapshot_counters()
    key1 = "/v1/evaluate|outbound|RULE-1|BLOCK"
    key2 = "/v1/evaluate|outbound|RULE-2|BLOCK"
    assert snap[key1] == 1
    assert snap[key2] == 1


def test_flush_clears_events(mock_telemetry):
    # Create a mock forwarder to track flushed events
    flushed_events = []

    class MockForwarder:
        def send_many(self, events):
            flushed_events.extend(events)

    mock_telemetry.forwarders = [MockForwarder()]

    # Record events
    evt1 = TelemetryEvent(
        ts="2025-01-01T00:00:00Z",
        endpoint="/v1/evaluate",
        direction="outbound",
        decision="ALLOW",
        shadow_mode=False,
        rule_ids=[],
        request_id="r4",
    )
    mock_telemetry.record_event(evt1)

    # Manually flush
    mock_telemetry.flush()

    # Check events are cleared but counters remain
    assert len(mock_telemetry.events) == 0
    assert len(flushed_events) == 1
    snap = mock_telemetry.snapshot_counters()
    key = "/v1/evaluate|outbound||ALLOW"
    assert key not in snap  # No rule_ids means no counter entry
