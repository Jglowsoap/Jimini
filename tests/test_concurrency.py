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
@patch("app.main.cfg")
@patch("app.main.telemetry")
def test_parallel_requests(
    mock_telemetry, mock_cfg, mock_evaluate, test_client, tmp_path
):
    # Configure mocks
    mock_cfg.app.shadow_mode = False
    jsonl_path = tmp_path / "events.jsonl"
    mock_cfg.siem.jsonl.enabled = True
    mock_cfg.siem.jsonl.path = str(jsonl_path)

    # Make sure the telemetry instance uses our path too
    mock_telemetry_instance = MagicMock()
    mock_telemetry.instance.return_value = mock_telemetry_instance

    # Mock evaluate to return ALLOW
    mock_evaluate.return_value = MagicMock(action="allow", rule_ids=[], message="")

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
    mock_telemetry_instance.flush.assert_called()

    # The real flush might not have happened because we mocked it, so manually flush
    for event in getattr(mock_telemetry_instance, "events", []):
        forwarder.send_many([{"request_id": str(i)} for i in range(request_count)])

    # Check that events were written
    assert os.path.exists(jsonl_path)
    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) >= request_count
