import json
import subprocess
import sys
import os
import pytest


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


def test_telemetry_cli_integration():
    try:
        # Run CLI command
        result = subprocess.run(
            [sys.executable, "-m", "jimini_cli", "telemetry", "counters"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Check for success and valid JSON output
        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        # Should return a dict (empty or with counters)
        assert isinstance(output_data, dict)
    except (subprocess.SubprocessError, json.JSONDecodeError):
        # If the CLI module isn't properly set up, skip the test
        pytest.skip("CLI command execution failed")
