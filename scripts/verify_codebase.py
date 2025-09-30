#!/usr/bin/env python3

import os
import sys
import subprocess
import yaml
import json


def run_command(cmd, env=None):
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, env={**os.environ, **(env or {})}
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_tests():
    print("Running tests...")
    code, stdout, stderr = run_command(["pytest", "-q"], {"PYTHONPATH": os.getcwd()})
    print(stdout)
    if stderr:
        print(stderr)
    return code == 0


def check_types():
    print("\nChecking types with mypy...")
    code, stdout, stderr = run_command(["mypy", "app", "jimini_cli"])
    if stdout or stderr:
        print("⚠️ Type warnings found:")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
    return code == 0


def check_rule_packs():
    print("\nChecking rule packs...")
    rules_path = os.environ.get("JIMINI_RULES_PATH", "policy_rules.yaml")
    try:
        with open(rules_path, "r") as f:
            rules = yaml.safe_load(f)

        if not isinstance(rules, list):
            print(f"❌ Error parsing {rules_path}: Rules must be a list")
            return False

        # Check for required fields in each rule
        missing_fields = []
        for i, rule in enumerate(rules):
            for field in ["id", "title", "severity", "action"]:
                if field not in rule:
                    missing_fields.append(
                        f"Rule #{i + 1} is missing required field: {field}"
                    )

        if missing_fields:
            for msg in missing_fields:
                print(f"❌ {msg}")
            return False

        print(f"✅ Successfully loaded {len(rules)} rules from {rules_path}")
        return True
    except Exception as e:
        print(f"❌ Error parsing {rules_path}: {str(e)}")
        return False


def check_endpoints():
    print("\nChecking API endpoints...")
    if not check_tests() or not check_rule_packs():
        print("⚠️ Skipping endpoint tests due to previous failures")
        return False

    # Simple smoke test of key endpoints
    server_running = False
    code, stdout, stderr = run_command(["curl", "-s", "http://localhost:9000/health"])
    if code == 0 and "ok" in stdout.lower():
        server_running = True

    if not server_running:
        print("⚠️ API server doesn't appear to be running")
        print("Start with: uvicorn app.main:app --host 0.0.0.0 --port 9000")
        return False

    # Test the evaluate endpoint
    payload = {
        "api_key": os.environ.get("JIMINI_API_KEY", "changeme"),
        "text": "test content",
        "endpoint": "/api/test",
        "direction": "inbound",
    }

    with open("test_payload.json", "w") as f:
        json.dump(payload, f)

    code, stdout, stderr = run_command(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            "-H",
            "Content-Type: application/json",
            "-d",
            "@test_payload.json",
            "http://localhost:9000/v1/evaluate",
        ]
    )

    os.unlink("test_payload.json")

    if code != 0:
        print(f"❌ Error testing /v1/evaluate endpoint: {stderr}")
        return False

    try:
        json.loads(stdout)
        print("✅ API endpoints working correctly")
        return True
    except Exception:  # Fixed: Removed unused variable 'e'
        print("❌ Invalid response from /v1/evaluate endpoint")
        return False


def print_summary(results):
    print("\n" + "=" * 50)
    print("CODEBASE VERIFICATION SUMMARY")
    print("=" * 50)

    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{name:15}: {icon}")

    print("=" * 50)

    if all(results.values()):
        print("✅ All checks passed - ready for deployment!")
    else:
        print("❌ Critical issues found - fix before proceeding to Phase 3")


if __name__ == "__main__":
    results = {
        "Tests passing": check_tests(),
        "Types clean": check_types(),
        "Rule packs": check_rule_packs(),
        "API endpoints": check_endpoints(),
    }

    print_summary(results)

    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)
    sys.exit(0 if all(results.values()) else 1)
