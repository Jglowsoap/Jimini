# tests/test_telemetry.py
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from app.telemetry import Telemetry, TelemetryEvent
from app.config import Config, AppConfig, NotifiersConfig, SlackConfig, SiemConfig, JsonlSiemConfig
from app.forwarders import JsonlForwarder

def test_telemetry_event_creation():
    """Test that telemetry events can be created."""
    evt = TelemetryEvent(
        ts="2025-01-01T00:00:00Z",
        endpoint="/v1/evaluate",
        direction="inbound",
        decision="ALLOW",
        shadow_mode=True,
        rule_ids=["TEST-1.0"],
        request_id="req_123",
        latency_ms=10.5
    )
    assert evt.endpoint == "/v1/evaluate"
    assert evt.decision == "ALLOW"
    assert evt.request_id == "req_123"

def test_telemetry_record_event():
    """Test that telemetry records events and updates counters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock config
        with patch('app.telemetry.get_config') as mock_get_config:
            cfg = Config()
            cfg.siem.jsonl.enabled = True
            cfg.siem.jsonl.path = os.path.join(tmpdir, "test_events.jsonl")
            mock_get_config.return_value = cfg
            
            tel = Telemetry(flush_sec=999)  # Don't auto-flush
            
            evt = TelemetryEvent(
                ts="2025-01-01T00:00:00Z",
                endpoint="/v1/evaluate",
                direction="outbound",
                decision="BLOCK",
                shadow_mode=False,
                rule_ids=["TEST-1.0"],
                request_id="req_123"
            )
            
            tel.record_event(evt)
            
            # Check counter
            counters = tel.snapshot_counters()
            assert "/v1/evaluate|outbound|TEST-1.0|BLOCK" in counters
            assert counters["/v1/evaluate|outbound|TEST-1.0|BLOCK"] == 1
            
            tel.stop()

def test_telemetry_flush():
    """Test that telemetry flushes events to forwarders."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jsonl_path = os.path.join(tmpdir, "test_events.jsonl")
        
        with patch('app.telemetry.get_config') as mock_get_config:
            cfg = Config()
            cfg.siem.jsonl.enabled = True
            cfg.siem.jsonl.path = jsonl_path
            mock_get_config.return_value = cfg
            
            tel = Telemetry(flush_sec=999)
            
            evt1 = TelemetryEvent(
                ts="2025-01-01T00:00:00Z",
                endpoint="/v1/evaluate",
                direction="outbound",
                decision="BLOCK",
                shadow_mode=False,
                rule_ids=["TEST-1.0"],
                request_id="req_123"
            )
            evt2 = TelemetryEvent(
                ts="2025-01-01T00:00:01Z",
                endpoint="/v1/evaluate",
                direction="outbound",
                decision="FLAG",
                shadow_mode=False,
                rule_ids=["TEST-2.0"],
                request_id="req_124"
            )
            
            tel.record_event(evt1)
            tel.record_event(evt2)
            tel.flush()
            
            # Read JSONL file and verify
            assert os.path.exists(jsonl_path)
            with open(jsonl_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 2
            event1 = json.loads(lines[0])
            event2 = json.loads(lines[1])
            
            assert event1['decision'] == 'BLOCK'
            assert event1['request_id'] == 'req_123'
            assert event2['decision'] == 'FLAG'
            assert event2['request_id'] == 'req_124'
            
            tel.stop()

def test_shadow_override_logic():
    """Test that shadow override logic works correctly."""
    # This will be tested in test_main.py with the full endpoint
    pass
