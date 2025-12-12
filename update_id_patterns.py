#!/usr/bin/env python3
"""
Update driver's license and federal ID patterns to match authoritative reference.
"""

import yaml
from datetime import datetime
import shutil

# Reference patterns from authoritative sources
state_dl_patterns = {
    "AL": r"^\d{7,8}$",
    "AK": r"^\d{7}$",
    "AZ": r"^(?:[A-Z]\d{8}|\d{9})$",
    "AR": r"^\d{9}$",
    "CA": r"^[A-Z]\d{7}$",
    "CO": r"^\d{9}$",
    "CT": r"^\d{9}$",
    "DE": r"^\d{7}$",
    "DC": r"^\d{7}$",
    "FL": r"^[A-Z]\d{12}$",
    "GA": r"^(?:\d{7}|\d{9})$",
    "HI": r"^(?:[A-Z]\d{8}|\d{9})$",
    "ID": r"^(?:[A-Z]{2}\d{6}[A-Z]|\d{9})$",
    "IL": r"^[A-Z]\d{11}$",
    "IN": r"^\d{10}$",
    "IA": r"^(?:\d{9}|\d{3}[A-Z]{2}\d{4})$",
    "KS": r"^(?:[A-Z]\d{8}|\d{9})$",
    "KY": r"^(?:[A-Z]\d{8}|[A-Z]\d{9}|\d{9})$",
    "LA": r"^\d{9}$",
    "ME": r"^(?:\d{7}|\d{7}[A-Z]|\d{8})$",
    "MD": r"^[A-Z]\d{12}$",
    "MA": r"^(?:[A-Z]\d{8}|\d{9})$",
    "MI": r"^(?:[A-Z]\d{10}|[A-Z]\d{12})$",
    "MN": r"^[A-Z]\d{12}$",
    "MS": r"^\d{9}$",
    "MO": r"^(?:\d{3}[A-Z]\d{6}|[A-Z]\d{5,9}|\d{8}[A-Z]{2}|\d{9}[A-Z]?|\d{9})$",
    "MT": r"^(?:[A-Z]{3}\d{10}|[A-Z]\d{8}|\d{9}|\d{13,14})$",
    "NE": r"^[A-Z]\d{6,8}$",
    "NV": r"^(?:\d{9,10}|\d{12}|X\d{8})$",
    "NH": r"^(?:\d{2}[A-Z]{3}\d{5})$",
    "NJ": r"^[A-Z]\d{14}$",
    "NM": r"^\d{8,9}$",
    "NY": r"^(?:[A-Z]\d{7}|\d{8,9}|\d{16}|[A-Z]\d{18}|[A-Z]{8})$",
    "NC": r"^\d{1,12}$",
    "ND": r"^(?:[A-Z]{3}\d{6}|\d{9})$",
    "OH": r"^(?:[A-Z]\d{4,8}|[A-Z]{2}\d{3,7}|\d{8})$",
    "OK": r"^(?:[A-Z]\d{9}|\d{9})$",
    "OR": r"^\d{1,9}$",
    "PA": r"^\d{8}$",
    "RI": r"^(?:\d{7}|[A-Z]\d{6})$",
    "SC": r"^\d{5,11}$",
    "SD": r"^(?:\d{6,10}|\d{12})$",
    "TN": r"^\d{7,9}$",
    "TX": r"^\d{7,8}$",
    "UT": r"^\d{4,10}$",
    "VT": r"^(?:\d{8}|\d{7}[A-Z])$",
    "VA": r"^(?:[A-Z]\d{8,11}|\d{9})$",
    "WA": r"^[A-Z0-9\*]{12}$",
    "WV": r"^(?:\d{7}|[A-Z]{1,2}\d{5,6})$",
    "WI": r"^[A-Z]\d{13}$",
    "WY": r"^\d{9,10}$"
}

# New federal ID rules to add
new_federal_ids = [
    {
        "id": "PII-PASSPORT-CARD-1.0",
        "title": "U.S. Passport Card Number",
        "description": "Detects U.S. Passport Card numbers (9 digits)",
        "severity": "high",
        "category": "pii",
        "pattern": r"^\d{9}$",
        "endpoints": ["*"],
        "action": "block",
        "shadow_override": None
    },
    {
        "id": "PII-DOD-ID-1.0",
        "title": "Department of Defense ID Number",
        "description": "Detects DoD ID numbers used on CAC (10 digits)",
        "severity": "high",
        "category": "pii",
        "pattern": r"^\d{10}$",
        "endpoints": ["*"],
        "action": "block",
        "shadow_override": None
    },
    {
        "id": "PII-ALIEN-NUMBER-1.0",
        "title": "Alien Registration Number (A-Number)",
        "description": "Detects USCIS A-Numbers (A followed by 8-9 digits)",
        "severity": "high",
        "category": "pii",
        "pattern": r"\bA\d{8,9}\b",
        "endpoints": ["*"],
        "action": "block",
        "shadow_override": None
    },
    {
        "id": "PII-USCIS-NUMBER-1.0",
        "title": "USCIS Number (Green Card)",
        "description": "Detects USCIS numbers printed on I-551 (13 alphanumeric)",
        "severity": "high",
        "category": "pii",
        "pattern": r"^[A-Z0-9]{13}$",
        "endpoints": ["*"],
        "action": "block",
        "shadow_override": None
    },
    {
        "id": "PII-USCIS-RECEIPT-1.0",
        "title": "USCIS Receipt Number",
        "description": "Detects USCIS receipt numbers (3 letters + 10 digits)",
        "severity": "medium",
        "category": "pii",
        "pattern": r"\b[A-Z]{3}\d{10}\b",
        "endpoints": ["*"],
        "action": "redact",
        "shadow_override": None
    },
    {
        "id": "PII-I94-1.0",
        "title": "Form I-94 Admission Number",
        "description": "Detects I-94 admission numbers (11 digits)",
        "severity": "high",
        "category": "pii",
        "pattern": r"^\d{11}$",
        "endpoints": ["*"],
        "action": "block",
        "shadow_override": None
    },
    {
        "id": "PII-SELECTIVE-SERVICE-1.0",
        "title": "Selective Service Number",
        "description": "Detects Selective Service registration numbers (10 digits)",
        "severity": "medium",
        "category": "pii",
        "pattern": r"^\d{10}$",
        "endpoints": ["*"],
        "action": "redact",
        "shadow_override": None
    },
    {
        "id": "PII-TWIC-1.0",
        "title": "Transportation Worker Identification Credential (TWIC)",
        "description": "Detects TWIC credential numbers (9 digits)",
        "severity": "high",
        "category": "pii",
        "pattern": r"^\d{9}$",
        "endpoints": ["*"],
        "action": "block",
        "shadow_override": None
    },
    {
        "id": "PII-PRECHECK-KTN-1.0",
        "title": "TSA PreCheck Known Traveler Number",
        "description": "Detects TSA PreCheck/Global Entry KTN (8-9 alphanumeric)",
        "severity": "medium",
        "category": "pii",
        "pattern": r"^[A-Z0-9]{8,9}$",
        "endpoints": ["*"],
        "action": "redact",
        "shadow_override": None
    }
]

def main():
    # Backup first
    backup_name = f"policy_rules_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
    shutil.copy('policy_rules.yaml', backup_name)
    print(f"✅ Backed up to {backup_name}")
    
    with open('policy_rules.yaml', 'r') as f:
        rules = yaml.safe_load(f)
    
    print(f"\nStarting with {len(rules)} rules")
    
    # Update DL patterns
    dl_updates = 0
    for state, new_pattern in state_dl_patterns.items():
        rule_id = f"PII-DL-{state}-1.0"
        for rule in rules:
            if rule.get('id') == rule_id:
                old_pattern = rule.get('pattern', '')
                if old_pattern != new_pattern:
                    rule['pattern'] = new_pattern
                    dl_updates += 1
                    print(f"  Updated {rule_id}: {old_pattern[:40]} → {new_pattern[:40]}")
                break
    
    print(f"\n✅ Updated {dl_updates} driver's license patterns")
    
    # Update existing federal patterns
    federal_updates = 0
    
    # Update SSN pattern (make it more precise)
    for rule in rules:
        if rule.get('id') in ['PII-SSN-1.0', 'SSN-1.0']:
            old = rule.get('pattern', '')
            if 'b' in old or '[-\\s]?' in old:  # Has word boundaries or optional separators
                rule['pattern'] = r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
                federal_updates += 1
                print(f"  Updated {rule['id']}: Standardized SSN pattern")
    
    # Update Passport patterns
    for rule in rules:
        if 'passport' in rule.get('id', '').lower() and rule.get('id') not in ['PII-PASSPORT-CARD-1.0']:
            old = rule.get('pattern', '')
            if old != r'\b\d{9}\b':
                rule['pattern'] = r'\b\d{9}\b'
                federal_updates += 1
                print(f"  Updated {rule['id']}: Standardized passport pattern")
    
    # Update EIN pattern
    for rule in rules:
        if rule.get('id') == 'PII-EIN-1.0':
            old = rule.get('pattern', '')
            rule['pattern'] = r'\b\d{2}[-\s]?\d{7}\b'
            federal_updates += 1
            print(f"  Updated {rule['id']}: Standardized EIN pattern")
    
    print(f"✅ Updated {federal_updates} federal ID patterns")
    
    # Add new federal ID rules
    print(f"\n✅ Adding {len(new_federal_ids)} new federal ID rules:")
    for new_rule in new_federal_ids:
        # Check if already exists
        exists = any(r.get('id') == new_rule['id'] for r in rules)
        if not exists:
            rules.append(new_rule)
            print(f"  + {new_rule['id']}: {new_rule['title']}")
        else:
            print(f"  ⚠️  {new_rule['id']}: Already exists, skipping")
    
    # Save updated rules
    with open('policy_rules.yaml', 'w') as f:
        yaml.dump(rules, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    # Count final distribution
    from collections import defaultdict
    action_counts = defaultdict(int)
    for rule in rules:
        action_counts[rule.get('action', 'unknown')] += 1
    
    print(f"\n{'='*60}")
    print(f"FINAL DISTRIBUTION ({len(rules)} total rules)")
    print(f"{'='*60}")
    for action, count in sorted(action_counts.items()):
        print(f"  {action}: {count}")
    
    print(f"\n✅ Updated policy_rules.yaml")
    print(f"\nNext steps:")
    print(f"  1. Review: git diff policy_rules.yaml")
    print(f"  2. Test: curl -X POST https://jimini-demo.fly.dev/v1/evaluate ...")
    print(f"  3. Commit and deploy")

if __name__ == '__main__':
    main()
