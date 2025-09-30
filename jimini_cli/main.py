# jimini_cli/main.py
import argparse
import json
import os
import sys
import subprocess
from typing import List

# Ensure we can import the local `app` package when running the CLI
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.enforcement import evaluate  # noqa: E402
from app.audit import verify_chain  # noqa: E402
from jimini_cli.loader import load_rules_from_file, load_rules_from_pack  # noqa: E402


def cmd_verify_audit(_args):
    result = verify_chain()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("valid") else 1)


# ---------- helpers ----------
def _load_store(args):
    if args.rule_pack:
        return load_rules_from_pack(args.rule_pack, args.version)
    if not args.rules:
        raise SystemExit("ERROR: provide --rules or --rule-pack")
    return load_rules_from_file(args.rules)


def _print_table(decision: str, rule_ids: List[str]):
    cols = ["decision", "rule_ids"]
    line = "+----------+-----------------------------+"
    print(line)
    print("| {:8} | {:27} |".format(cols[0], cols[1]))
    print(line)
    rules_str = ", ".join(rule_ids) if rule_ids else "-"
    print("| {:8} | {:27} |".format(decision, rules_str[:27]))
    print(line)


def _print_sarif(decision: str, rule_ids: List[str]):
    sarif = {
        "version": "2.1.0",
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Jimini",
                        "informationUri": "https://example.local/jimini",
                    }
                },
                "results": [
                    {
                        "ruleId": rid,
                        "level": "error"
                        if decision == "block"
                        else "warning"
                        if decision == "flag"
                        else "note",
                        "message": {
                            "text": f"Rule {rid} triggered. Decision: {decision}."
                        },
                    }
                    for rid in (rule_ids or [])
                ],
            }
        ],
    }
    print(json.dumps(sarif, indent=2))


# ---------- commands ----------
def cmd_lint(args):
    try:
        store = _load_store(args)
        count = len(store)
        source = args.rule_pack or args.rules
        print(f"OK: loaded {count} rules from {source}")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)


def cmd_test(args):
    try:
        store = _load_store(args)
        decision, rule_ids, enforce_even_in_shadow = evaluate(
            text=args.text,
            agent_id=args.agent_id,
            rules_store=store,
            direction=args.direction,
            endpoint=args.endpoint,
        )

        payload = {
            "decision": decision,
            "rule_ids": rule_ids,
            "shadow": bool(args.shadow),
            "enforce_even_in_shadow": enforce_even_in_shadow,
        }

        if args.format == "json":
            print(json.dumps(payload, indent=2))
        elif args.format == "table":
            _print_table(decision, rule_ids)
        elif args.format == "sarif":
            _print_sarif(decision, rule_ids)
        else:
            print(json.dumps(payload, indent=2))

        if args.shadow:
            sys.exit(0)
        sys.exit(0 if decision != "block" else 1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)


def cmd_run_local(args):
    """
    Boot your FastAPI gateway locally with chosen rules.
    Shadow mode is passed via env (JIMINI_SHADOW=1) and respected by app.main.
    """
    env = os.environ.copy()
    if args.rule_pack and not args.rules:
        pack_path = os.path.abspath(
            os.path.join(
                REPO_ROOT, "packs", args.rule_pack.lower(), f"{args.version}.yaml"
            )
        )
        if not os.path.exists(pack_path):
            raise SystemExit(f"Pack not found: {pack_path}")
        # Align with API: set only JIMINI_RULES_PATH
        env["JIMINI_RULES_PATH"] = pack_path
    else:
        rules_abs = os.path.abspath(args.rules)
        env["JIMINI_RULES_PATH"] = rules_abs
    env["PYTHONPATH"] = REPO_ROOT + (os.pathsep + env.get("PYTHONPATH", ""))

    if args.shadow:
        env["JIMINI_SHADOW"] = "1"

    host = args.host or "0.0.0.0"
    port = str(args.port or 9000)
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--host",
        host,
        "--port",
        port,
    ]
    print(
        f"Launching Jimini on http://{host}:{port} with JIMINI_RULES_PATH={env['JIMINI_RULES_PATH']}"
        + (" (shadow mode)" if args.shadow else "")
    )
    subprocess.run(cmd, env=env, check=False)


def build_parser():
    p = argparse.ArgumentParser(prog="jimini", description="Jimini CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    # lint
    p_lint = sub.add_parser("lint", help="Validate a rules file or pack")
    p_lint.add_argument("--rules", help="Path to YAML rules file")
    p_lint.add_argument(
        "--rule-pack",
        choices=["illinois", "cjis", "hipaa", "pci", "secrets"],
        help="Built-in rule pack",
    )
    p_lint.add_argument("--version", default="v1", help="Pack version (default v1)")
    p_lint.set_defaults(func=cmd_lint)

    # test
    p_test = sub.add_parser("test", help="Evaluate sample text against rules")
    p_test.add_argument("--rules", help="Path to YAML rules file")
    p_test.add_argument(
        "--rule-pack",
        choices=["illinois", "cjis", "hipaa", "pci", "secrets"],
        help="Built-in rule pack",
    )
    p_test.add_argument("--version", default="v1")
    p_test.add_argument("--text", required=True, help="Sample text to evaluate")
    p_test.add_argument("--agent-id", default="cli:test", help="Agent/User id context")
    p_test.add_argument("--direction", choices=["inbound", "outbound"], default=None)
    p_test.add_argument("--endpoint", default=None, help="Endpoint path context")
    p_test.add_argument("--format", choices=["json", "table", "sarif"], default="json")
    p_test.add_argument(
        "--shadow", action="store_true", help="Simulate (never nonzero exit)"
    )
    p_test.set_defaults(func=cmd_test)

    # run-local
    p_run = sub.add_parser("run-local", help="Run local gateway with rules or pack")
    p_run.add_argument("--rules", help="Path to YAML rules file")
    p_run.add_argument(
        "--rule-pack",
        choices=["illinois", "cjis", "hipaa", "pci", "secrets"],
        help="Built-in rule pack",
    )
    p_run.add_argument("--version", default="v1")
    p_run.add_argument("--host", default="0.0.0.0")
    p_run.add_argument("--port", type=int, default=9000)
    p_run.add_argument(
        "--shadow", action="store_true", help="Simulate enforcement (no blocking)"
    )
    p_run.set_defaults(func=cmd_run_local)

    # verify
    p_verify = sub.add_parser("verify-audit", help="Verify local audit hash chain")
    p_verify.set_defaults(func=cmd_verify_audit)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
