# tests/test_forwarders.py
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from app.forwarders import JsonlForwarder, SplunkHECForwarder, ElasticForwarder

def test_jsonl_forwarder():
    """Test JSONL forwarder writes events correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.jsonl")
        forwarder = JsonlForwarder(path)
        
        events = [
            {"ts": "2025-01-01T00:00:00Z", "decision": "BLOCK"},
            {"ts": "2025-01-01T00:00:01Z", "decision": "FLAG"},
        ]
        
        forwarder.send_many(events)
        
        # Read and verify
        assert os.path.exists(path)
        with open(path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        e1 = json.loads(lines[0])
        e2 = json.loads(lines[1])
        assert e1["decision"] == "BLOCK"
        assert e2["decision"] == "FLAG"

def test_splunk_hec_forwarder():
    """Test Splunk HEC forwarder sends correct payload."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        forwarder = SplunkHECForwarder(
            url="https://splunk.example.com:8088/services/collector",
            token="test-token",
            sourcetype="jimini:event"
        )
        
        events = [
            {"ts": "2025-01-01T00:00:00Z", "decision": "BLOCK"},
        ]
        
        forwarder.send_many(events)
        
        # Verify urlopen was called
        assert mock_urlopen.called
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        
        # Verify request headers
        assert request.get_header("Authorization") == "Splunk test-token"
        assert request.get_header("Content-type") == "application/json"
        
        # Verify payload structure
        data = request.data.decode('utf-8')
        payload = json.loads(data)
        assert payload["event"]["decision"] == "BLOCK"
        assert payload["sourcetype"] == "jimini:event"

def test_elastic_forwarder():
    """Test Elasticsearch forwarder sends correct payload."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        forwarder = ElasticForwarder(
            url="https://elastic.example.com:9200/jimini-events/_doc",
            auth=("user", "pass")
        )
        
        events = [
            {"ts": "2025-01-01T00:00:00Z", "decision": "BLOCK"},
        ]
        
        forwarder.send_many(events)
        
        # Verify urlopen was called
        assert mock_urlopen.called
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        
        # Verify request headers
        assert request.get_header("Content-type") == "application/json"
        assert "Authorization" in request.headers
        assert request.get_header("Authorization").startswith("Basic ")
        
        # Verify payload
        data = request.data.decode('utf-8')
        payload = json.loads(data)
        assert payload["decision"] == "BLOCK"
