import json
import base64
from unittest.mock import patch, MagicMock

from app.forwarders.splunk_forwarder import SplunkHECForwarder
from app.forwarders.elastic_forwarder import ElasticForwarder


def test_splunk_hec_forwarder_headers_and_payload():
    # Mock urlopen
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Create forwarder and send events
        forwarder = SplunkHECForwarder(
            url="https://splunk.example.com:8088/services/collector",
            token="test-token",
            sourcetype="jimini:event",
        )

        events = [
            {"ts": "2023-01-01T00:00:00Z", "decision": "BLOCK"},
            {"ts": "2023-01-01T00:00:01Z", "decision": "ALLOW"},
        ]

        forwarder.send_many(events)

        # Get request from mock
        args, kwargs = mock_urlopen.call_args
        request = args[0]

        # Check headers
        assert request.get_header("Content-type") == "application/json"
        assert request.get_header("Authorization") == "Splunk test-token"

        # Check payload format
        payload_lines = request.data.decode().split("\n")
        assert len(payload_lines) == 2

        # Each line should be a JSON object with event and sourcetype
        for i, line in enumerate(payload_lines):
            data = json.loads(line)
            assert "event" in data
            assert "sourcetype" in data
            assert data["sourcetype"] == "jimini:event"
            assert data["event"]["ts"] == events[i]["ts"]
            assert data["event"]["decision"] == events[i]["decision"]


def test_elastic_forwarder_headers_and_auth():
    # Mock urlopen
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Create forwarder with auth and send an event
        forwarder = ElasticForwarder(
            url="https://elastic.example.com:9200/jimini-events/_doc",
            auth=("user", "pass"),
        )

        event = {"ts": "2023-01-01T00:00:00Z", "decision": "BLOCK"}
        forwarder.send_many([event])

        # Get request from mock
        args, kwargs = mock_urlopen.call_args
        request = args[0]

        # Check headers
        assert request.get_header("Content-type") == "application/json"

        # Check Basic Auth
        auth_header = request.get_header("Authorization")
        assert auth_header.startswith("Basic ")

        # Decode and verify the base64 part
        token = base64.b64decode(auth_header[6:]).decode("utf-8")
        assert token == "user:pass"

        # Check payload format (direct JSON)
        payload = json.loads(request.data.decode())
        assert payload["ts"] == event["ts"]
        assert payload["decision"] == event["decision"]
