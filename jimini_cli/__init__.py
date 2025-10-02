__all__ = []

import argparse
import json
import sys
import time
from pathlib import Path


def verify_audit(args):
    print("Verifying audit chain...")
    # Implementation would go here
    return True


def main():
    parser = argparse.ArgumentParser(description="Jimini CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # verify-audit command
    subparsers.add_parser("verify-audit", help="Verify the audit log chain integrity")

    # Lint rules
    subparsers.add_parser("lint", help="Lint rules file")

    # Test rules
    test_parser = subparsers.add_parser("test", help="Test rules against text")
    test_parser.add_argument("--rule-pack", help="Rule pack name to test")
    test_parser.add_argument("--text", help="Text to test against")
    test_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # Run local server
    local_parser = subparsers.add_parser("run-local", help="Run a local Jimini server")
    local_parser.add_argument("--rules", help="Path to rules file")
    local_parser.add_argument("--port", type=int, default=9000, help="Port to run on")
    local_parser.add_argument(
        "--shadow", action="store_true", help="Enable shadow mode"
    )

    # Telemetry commands
    telemetry_parser = subparsers.add_parser("telemetry", help="Telemetry operations")
    telemetry_subparsers = telemetry_parser.add_subparsers(
        dest="telemetry_command", help="Telemetry command"
    )

    telemetry_subparsers.add_parser(
        "counters", help="Display current telemetry counters"
    )
    telemetry_subparsers.add_parser("flush", help="Force flush of telemetry events")

    tail_parser = telemetry_subparsers.add_parser(
        "tail", help="Tail telemetry event logs"
    )
    tail_parser.add_argument(
        "--file", default="logs/jimini_events.jsonl", help="Path to event log file"
    )

    args = parser.parse_args()

    # Handle telemetry commands
    if args.command == "telemetry":
        # Import here to avoid circular imports
        from app.telemetry import Telemetry

        tel = Telemetry.instance()

        if args.telemetry_command == "counters":
            print(json.dumps(tel.snapshot_counters(), indent=2))

        elif args.telemetry_command == "flush":
            tel.flush()
            print("Telemetry events flushed")

        elif args.telemetry_command == "tail":
            path = Path(args.file)
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.touch()

            print(f"Tailing {path}. Press Ctrl+C to stop.")
            with open(path, "r", encoding="utf-8") as f:
                f.seek(0, 2)  # Move to end of file
                try:
                    while True:
                        line = f.readline()
                        if not line:
                            time.sleep(0.5)
                            continue
                        try:
                            data = json.loads(line)
                            print(json.dumps(data, indent=2))
                        except json.JSONDecodeError:
                            print(line, end="")
                except KeyboardInterrupt:
                    print("\nStopping tail")

    if args.command == "verify-audit":
        result = verify_audit(args)
        sys.exit(0 if result else 1)
    elif args.command == "telemetry":
        # Telemetry commands are already handled above
        sys.exit(0)
    elif not args.command:
        parser.print_help()
        sys.exit(1)
    else:
        print(f"Command {args.command} not implemented yet")
        sys.exit(1)


if __name__ == "__main__":
    main()
    main()
