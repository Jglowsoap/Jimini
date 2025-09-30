import json
from app.telemetry import TelemetryEvent
from app.forwarders.jsonl_forwarder import JsonlForwarder


def test_event_fields(tmp_path):
    # Create a forwarder with a temp file
    jsonl_path = tmp_path / "events.jsonl"
    forwarder = JsonlForwarder(str(jsonl_path))

    # Create sample events
    events = [
        TelemetryEvent(
            ts="2023-01-01T00:00:00Z",
            endpoint="/v1/evaluate",
            direction="inbound",
            decision="ALLOW",
            shadow_mode=False,
            rule_ids=[],
            request_id="req1",
        ),
        TelemetryEvent(
            ts="2023-01-01T00:00:01Z",
            endpoint="/v1/evaluate",
            direction="outbound",
            decision="BLOCK",
            shadow_mode=True,
            rule_ids=["RULE-1", "RULE-2"],
            request_id="req2",
            latency_ms=15.3,
            meta={"raw_decision": "BLOCK"},
        ),
    ]

    # Convert to dictionaries and write to JSONL
    event_dicts = []
    for event in events:
        event_dict = {
            "ts": event.ts,
            "endpoint": event.endpoint,
            "direction": event.direction,
            "decision": event.decision,
            "shadow_mode": event.shadow_mode,
            "rule_ids": event.rule_ids,
        }
        if event.request_id:
            event_dict["request_id"] = event.request_id
        if event.latency_ms is not None:
            event_dict["latency_ms"] = event.latency_ms
        if event.meta:
            event_dict["meta"] = event.meta
        event_dicts.append(event_dict)

    forwarder.send_many(event_dicts)

    # Read back and validate
    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == 2

    for line in lines:
        event = json.loads(line)
        # Check required fields
        for key in [
            "ts",
            "endpoint",
            "direction",
            "decision",
            "shadow_mode",
            "rule_ids",
        ]:
            assert key in event

        # Validate field types
        assert isinstance(event["ts"], str)
        assert isinstance(event["endpoint"], str)
        assert isinstance(event["direction"], str)
        assert isinstance(event["decision"], str)
        assert isinstance(event["shadow_mode"], bool)
        assert isinstance(event["rule_ids"], list)

        # Optional fields have correct types when present
        if "request_id" in event:
            assert isinstance(event["request_id"], str)
        if "latency_ms" in event:
            assert isinstance(event["latency_ms"], (int, float))
        if "meta" in event:
            assert isinstance(event["meta"], dict)
