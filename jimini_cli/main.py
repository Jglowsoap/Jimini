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
from app.telemetry import Telemetry  # noqa: E402
from app.deadletter import deadletter_queue  # noqa: E402
from app.circuit_breaker import circuit_manager  # noqa: E402
from jimini_cli.loader import load_rules_from_file, load_rules_from_pack  # noqa: E402


def cmd_verify_audit(_args):
    result = verify_chain()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("valid") else 1)


def cmd_telemetry_counters(_args):
    """Get telemetry counters"""
    try:
        telemetry = Telemetry.instance()
        counters = telemetry.snapshot_counters()
        print(json.dumps(counters, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_telemetry_flush(_args):
    """Flush telemetry events to forwarders"""
    try:
        telemetry = Telemetry.instance()
        telemetry.flush()
        print("Telemetry events flushed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_replay(args):
    """Replay events from dead letter queue"""
    try:
        target = getattr(args, 'target', None)
        source = getattr(args, 'from_file', 'logs/deadletter.jsonl')
        
        # Read events from dead letter queue
        events = deadletter_queue.read_events(target=target)
        
        if not events:
            print(f"No events found in dead letter queue" + (f" for target {target}" if target else ""))
            return
        
        print(f"Found {len(events)} events in dead letter queue" + (f" for target {target}" if target else ""))
        
        # Group events by target for replay
        target_events = {}
        for event in events:
            if event.target not in target_events:
                target_events[event.target] = []
            target_events[event.target].append(event.original_event)
        
        # Replay events using telemetry system
        telemetry = Telemetry.instance()
        success_count = 0
        failure_count = 0
        
        for target_name, target_event_list in target_events.items():
            try:
                # Find appropriate forwarder
                forwarder = None
                for fwd in telemetry.forwarders:
                    if fwd.name == target_name:
                        forwarder = fwd
                        break
                
                if forwarder:
                    print(f"Replaying {len(target_event_list)} events to {target_name}...")
                    forwarder.send_many(target_event_list)
                    success_count += len(target_event_list)
                    
                    # Clear successfully replayed events
                    deadletter_queue.clear_target(target_name)
                    print(f"✅ Successfully replayed events to {target_name}")
                else:
                    print(f"❌ No forwarder found for target {target_name}")
                    failure_count += len(target_event_list)
            
            except Exception as e:
                print(f"❌ Failed to replay events to {target_name}: {e}")
                failure_count += len(target_event_list)
        
        print(f"Replay complete: {success_count} successful, {failure_count} failed")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_deadletter_stats(_args):
    """Show dead letter queue statistics"""
    try:
        stats = deadletter_queue.get_stats()
        print(json.dumps(stats, indent=2))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_circuit_status(_args):
    """Show circuit breaker status"""
    try:
        all_states = circuit_manager.get_all_states()
        all_closed = circuit_manager.are_all_closed()
        
        result = {
            "all_circuits_closed": all_closed,
            "circuit_states": all_states,
            "summary": f"{len([s for s in all_states.values() if s == 'closed'])} closed, {len([s for s in all_states.values() if s == 'open'])} open"
        }
        
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


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

    # telemetry
    p_telemetry = sub.add_parser("telemetry", help="Telemetry operations")
    telemetry_sub = p_telemetry.add_subparsers(dest="telemetry_cmd", required=True)

    # telemetry counters
    p_tel_counters = telemetry_sub.add_parser("counters", help="Get telemetry counters")
    p_tel_counters.set_defaults(func=cmd_telemetry_counters)

    # telemetry flush
    p_tel_flush = telemetry_sub.add_parser("flush", help="Flush telemetry events to forwarders")
    p_tel_flush.set_defaults(func=cmd_telemetry_flush)

    # replay
    p_replay = sub.add_parser("replay", help="Replay events from dead letter queue")
    p_replay.add_argument("--target", help="Target forwarder to replay (optional)")
    p_replay.add_argument("--from-file", default="logs/deadletter.jsonl", help="Dead letter file path")
    p_replay.set_defaults(func=cmd_replay)

    # deadletter
    p_deadletter = sub.add_parser("deadletter", help="Dead letter queue operations")
    deadletter_sub = p_deadletter.add_subparsers(dest="deadletter_cmd", required=True)
    
    p_dl_stats = deadletter_sub.add_parser("stats", help="Show dead letter queue statistics")
    p_dl_stats.set_defaults(func=cmd_deadletter_stats)

    # circuit
    p_circuit = sub.add_parser("circuit", help="Circuit breaker operations")
    circuit_sub = p_circuit.add_subparsers(dest="circuit_cmd", required=True)
    
    p_circuit_status = circuit_sub.add_parser("status", help="Show circuit breaker status")
    p_circuit_status.set_defaults(func=cmd_circuit_status)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


def admin_main():
    """Entry point for jimini-admin console script with enhanced admin features."""
    from app.__version__ import __version__, get_version_info
    
    parser = argparse.ArgumentParser(
        prog="jimini-admin",
        description=f"Jimini Administration Tools v{__version__}"
    )
    
    sub = parser.add_subparsers(dest="admin_cmd", required=True, help="Admin commands")
    
    # Version information
    p_version = sub.add_parser("version", help="Show detailed version information")
    p_version.set_defaults(func=lambda _: print(json.dumps(get_version_info(), indent=2)))
    
    # System status
    p_status = sub.add_parser("status", help="Show comprehensive system status")
    p_status.set_defaults(func=cmd_admin_status)
    
    # Security management
    p_security = sub.add_parser("security", help="Security and compliance management")
    security_sub = p_security.add_subparsers(dest="security_cmd", required=True)
    
    p_sec_status = security_sub.add_parser("status", help="Security status")
    p_sec_status.set_defaults(func=cmd_security_status)
    
    p_sec_rbac = security_sub.add_parser("rbac", help="RBAC configuration")
    p_sec_rbac.set_defaults(func=cmd_rbac_status)
    
    # Circuit breaker admin
    p_circuit_admin = sub.add_parser("circuit", help="Circuit breaker administration")
    circuit_admin_sub = p_circuit_admin.add_subparsers(dest="circuit_admin_cmd", required=True)
    
    p_circuit_reset_all = circuit_admin_sub.add_parser("reset-all", help="Reset all circuit breakers")
    p_circuit_reset_all.set_defaults(func=cmd_circuit_reset_all)
    
    # Configuration
    p_config = sub.add_parser("config", help="Configuration management")
    config_sub = p_config.add_subparsers(dest="config_cmd", required=True)
    
    p_config_show = config_sub.add_parser("show", help="Show current configuration")
    p_config_show.set_defaults(func=cmd_config_show)
    
    p_config_validate = config_sub.add_parser("validate", help="Validate configuration")
    p_config_validate.set_defaults(func=cmd_config_validate)
    
    args = parser.parse_args()
    args.func(args)


def cmd_admin_status(_args):
    """Show comprehensive system status."""
    from config.loader import get_current_config
    
    config = get_current_config()
    telemetry = Telemetry.instance()
    
    status = {
        "system": {
            "status": "operational",
            "version": get_version_info()["version"],
            "config_valid": config is not None
        },
        "telemetry": telemetry.snapshot_counters(),
        "circuit_breakers": circuit_manager.get_all_status(),
        "dead_letter": deadletter_queue.get_stats(),
        "configuration": {
            "shadow_mode": config.app.shadow_mode if config and config.app else False,
            "rules_loaded": len(getattr(sys.modules.get('app.rules_loader', {}), 'rules_store', [])),
        }
    }
    
    print(json.dumps(status, indent=2))


def cmd_security_status(_args):
    """Show security status."""
    try:
        # This would normally call the admin security endpoint
        # For CLI, we replicate the logic
        from app.redaction import PIIRedactor
        from app.rbac import RBACManager
        
        redactor = PIIRedactor()
        rbac = RBACManager()
        
        status = {
            "rbac_status": {
                "enabled": False,  # Default for CLI
                "supported_roles": ["ADMIN", "REVIEWER", "SUPPORT", "USER"],
                "role_hierarchy": rbac.role_hierarchy
            },
            "redaction_summary": {
                "pii_processing_enabled": False,
                "total_rules": len(redactor.rules),
                "redaction_rules": [
                    {"name": rule.name, "replacement": rule.replacement}
                    for rule in redactor.rules
                ]
            },
            "compliance_features": {
                "audit_chain": "enabled",
                "pii_redaction": "enabled", 
                "data_retention": "30 days"
            }
        }
        
        print(json.dumps(status, indent=2))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_rbac_status(_args):
    """Show RBAC configuration."""
    from app.rbac import RBACManager
    
    rbac = RBACManager()
    status = {
        "rbac_configuration": {
            "supported_roles": ["ADMIN", "REVIEWER", "SUPPORT", "USER"],
            "role_hierarchy": rbac.role_hierarchy,
            "jwt_configured": False  # CLI context
        }
    }
    
    print(json.dumps(status, indent=2))


def cmd_circuit_reset_all(_args):
    """Reset all circuit breakers."""
    try:
        reset_count = circuit_manager.reset_all()
        print(f"Reset {reset_count} circuit breakers")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_config_show(_args):
    """Show current configuration."""
    from config.loader import get_current_config, mask_secrets
    
    try:
        config = get_current_config()
        if config:
            # Convert to dict and mask secrets
            config_dict = config.model_dump()
            masked = mask_secrets(config_dict)
            print(json.dumps(masked, indent=2))
        else:
            print("No configuration loaded")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_config_validate(_args):
    """Validate configuration."""
    from config.loader import get_current_config
    
    try:
        config = get_current_config()
        if config:
            print("✅ Configuration is valid")
            print(f"App configuration: shadow_mode={config.app.shadow_mode if config.app else 'undefined'}")
            print(f"Loaded integrations: {len([k for k, v in config.model_dump().items() if k != 'app' and v])}")
        else:
            print("❌ Configuration validation failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
