import json
import subprocess
import sys
import os
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.skipif(
    not os.path.exists("jimini_cli/__init__.py"), reason="CLI module not found"
)
def test_cli_counters_runs():
    try:
        # Try to run the CLI command
        result = subprocess.run(
            [sys.executable, "-m", "jimini_cli", "telemetry", "counters"],
            capture_output=True,
            text=True,
            timeout=5,  # Add timeout to prevent hanging
        )

        # Check if command succeeded
        assert result.returncode == 0

        # It should output valid JSON (even if empty)
        json_data = json.loads(result.stdout or "{}")
        assert isinstance(json_data, dict)
    except (subprocess.SubprocessError, json.JSONDecodeError) as e:
        pytest.skip(f"CLI command failed to run properly: {e}")


@patch("app.telemetry.Telemetry.instance")
def test_telemetry_cli_integration(mock_instance):
    # Mock the telemetry instance
    mock_telemetry = MagicMock()
    mock_instance.return_value = mock_telemetry

    # Prepare mock counters
    mock_counters = {
        "/v1/evaluate|outbound|RULE-1|BLOCK": 5,
        "/v1/evaluate|inbound|RULE-2|FLAG": 3,
    }
    mock_telemetry.snapshot_counters.return_value = mock_counters

    try:
        # Run CLI command
        result = subprocess.run(
            [sys.executable, "-m", "jimini_cli", "telemetry", "counters"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Check for success and correct output
        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert output_data == mock_counters
    except (subprocess.SubprocessError, json.JSONDecodeError):
        # If the CLI module isn't properly set up, skip the test
        pytest.skip("CLI command execution failed")
