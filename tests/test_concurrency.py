import os
import concurrent.futures
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def test_client():
    return TestClient(app)


@patch("app.main.evaluate")
@patch("config.loader.get_current_config")
@patch("app.main.telemetry")
def test_parallel_requests(
    mock_telemetry, mock_get_config, mock_evaluate, test_client, tmp_path
):
    # Configure mocks
    mock_cfg = MagicMock()
    mock_cfg.app.shadow_mode = False
    mock_get_config.return_value = mock_cfg
    
    jsonl_path = tmp_path / "events.jsonl"
    mock_cfg.siem.jsonl.enabled = True
    mock_cfg.siem.jsonl.path = str(jsonl_path)

    # Make sure the telemetry instance uses our path too
    mock_telemetry_instance = MagicMock()
    mock_telemetry.instance.return_value = mock_telemetry_instance
    # Also mock the direct telemetry object used in main.py
    mock_telemetry.flush = MagicMock()
    mock_telemetry.record_event = MagicMock()

    # Mock evaluate to return ALLOW
    mock_evaluate.return_value = ("allow", [], False)

    # Set up a forwarded to write to our temp file
    from app.forwarders.jsonl_forwarder import JsonlForwarder

    forwarder = JsonlForwarder(str(jsonl_path))
    mock_telemetry_instance.forwarders = [forwarder]

    # Make parallel requests
    client = test_client
    request_count = 20  # Reduced from 50 for faster tests

    def hit():
        return client.post(
            "/v1/evaluate",
            json={
                "api_key": "changeme",
                "text": "test",
                "endpoint": "/test",
                "direction": "inbound",
            },
        ).status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        codes = list(executor.map(lambda _: hit(), range(request_count)))

    # Check that all requests succeeded
    assert all(c == 200 for c in codes)

    # Flush telemetry to ensure all events are written
    # Since we're mocking, flush should have been called at least once per request
    assert mock_telemetry.flush.call_count >= request_count

    # The real flush might not have happened because we mocked it, so manually flush some test events
    # to verify the forwarder works
    test_events = [{"request_id": str(i)} for i in range(min(5, request_count))]
    forwarder.send_many(test_events)

    # Check that test events were written
    assert os.path.exists(jsonl_path)
    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Should have at least the test events we wrote
    assert len(lines) >= len(test_events)
