#!/usr/bin/env python3
"""
Demo script for Phase 3 Telemetry & Integration features.
Shows how telemetry, shadow mode, and SIEM integration work.
"""
import json
import os
import time

# Setup
print("=" * 60)
print("PHASE 3: Telemetry & Integration Demo")
print("=" * 60)

# 1. Show config
print("\n1. Configuration (jimini.config.yaml)")
print("-" * 60)
from app.config import get_config
cfg = get_config()
print(f"   Shadow Mode:      {cfg.app.shadow_mode}")
print(f"   Shadow Overrides: {cfg.app.shadow_overrides}")
print(f"   JSONL Enabled:    {cfg.siem.jsonl.enabled}")
print(f"   JSONL Path:       {cfg.siem.jsonl.path}")
print(f"   Slack Enabled:    {cfg.notifiers.slack.enabled}")
print(f"   OTEL Enabled:     {cfg.otel.enabled}")

# 2. Show telemetry
print("\n2. Telemetry System")
print("-" * 60)
from app.telemetry import Telemetry, TelemetryEvent
from app.util import now_iso, gen_request_id

tel = Telemetry.instance()
print(f"   Active Forwarders: {len(tel.forwarders)}")
print(f"   Background Thread: Running (flush every {tel.flush_sec}s)")

# 3. Record sample events
print("\n3. Recording Sample Events")
print("-" * 60)

events = [
    ("BLOCK", ["IL-AI-4.2"], "SSN: 123-45-6789"),
    ("FLAG", ["EMAIL-1.0"], "user@example.com"),
    ("ALLOW", [], "Normal text"),
]

for decision, rules, text in events:
    evt = TelemetryEvent(
        ts=now_iso(),
        endpoint="/v1/evaluate",
        direction="outbound",
        decision=decision,
        shadow_mode=cfg.app.shadow_mode,
        rule_ids=rules,
        request_id=gen_request_id(),
        latency_ms=round(time.time() % 100, 2)
    )
    tel.record_event(evt)
    print(f"   ✓ Recorded: {decision:6} {rules or '[no rules]'}")

# 4. Show counters
print("\n4. Telemetry Counters")
print("-" * 60)
counters = tel.snapshot_counters()
for key, count in counters.items():
    print(f"   {key}: {count}")

# 5. Flush to forwarders
print("\n5. Flushing Events to Forwarders")
print("-" * 60)
tel.flush()
print(f"   ✓ Flushed to {len(tel.forwarders)} forwarder(s)")

# 6. Check JSONL output
print("\n6. JSONL Output (last 3 events)")
print("-" * 60)
if os.path.exists(cfg.siem.jsonl.path):
    with open(cfg.siem.jsonl.path, 'r') as f:
        lines = f.readlines()
    
    for line in lines[-3:]:
        event = json.loads(line)
        print(f"   {event['ts'][:19]} | {event['decision']:6} | {event['direction']:8} | {event['rule_ids']}")
else:
    print("   (No JSONL file found)")

# 7. Shadow override logic
print("\n7. Shadow Mode with Overrides")
print("-" * 60)
print(f"   Shadow Mode:      {cfg.app.shadow_mode}")
print(f"   Shadow Overrides: {cfg.app.shadow_overrides}")
print()
print("   Rule IL-AI-4.2 → IN overrides → ENFORCES (blocks)")
print("   Rule EMAIL-1.0 → NOT in overrides → ALLOWS (shadowed)")

# 8. CLI commands
print("\n8. CLI Commands Available")
print("-" * 60)
print("   jimini telemetry counters  # View current counters")
print("   jimini telemetry flush     # Force flush to forwarders")
print("   jimini telemetry tail      # Tail JSONL events")

print("\n" + "=" * 60)
print("✅ Phase 3 Demo Complete!")
print("=" * 60)
print()
print("Next steps:")
print("  - View counters: jimini telemetry counters")
print("  - Tail events:   jimini telemetry tail")
print("  - Configure Slack/Splunk/Elastic in jimini.config.yaml")
print()
