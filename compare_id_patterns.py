#!/usr/bin/env python3
"""
Compare provided DL/Federal ID patterns against current policy_rules.yaml
"""

import yaml
import json

# Reference patterns from user
state_dl_reference = {
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
    "NH": r"^(?:\d{2}[A-Z]{3}\d{2}\d{2}\d)$",
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

federal_id_reference = {
    "SSN": {"regex": r"^\d{9}$", "display": "NNN-NN-NNNN"},
    "Passport": {"regex": r"^\d{9}$", "display": "NNNNNNNNN"},
    "Passport Card": {"regex": r"^\d{9}$", "display": "NNNNNNNNN"},
    "DoD ID": {"regex": r"^\d{10}$", "display": "NNNNNNNNNN"},
    "A-Number": {"regex": r"^A\d{8,9}$", "display": "A######## or A#########"},
    "USCIS Number": {"regex": r"^[A-Z0-9]{13}$", "display": "XXXXXXXXXXXXX"},
    "USCIS Receipt": {"regex": r"^[A-Z]{3}\d{10}$", "display": "AAAYYDDDNNNNN"},
    "I-94": {"regex": r"^\d{11}$", "display": "NNNNNNNNNNN"},
    "Selective Service": {"regex": r"^\d{10}$", "display": "NNNNNNNNNN"},
    "TWIC": {"regex": r"^\d{9}$", "display": "NNNNNNNNN"},
    "EIN": {"regex": r"^\d{9}$", "display": "NN-NNNNNNN"},
    "PreCheck KTN": {"regex": r"^[A-Z0-9]{8,9}$", "display": "XXXXXXXX"}
}

with open('policy_rules.yaml', 'r') as f:
    current_rules = yaml.safe_load(f)

print("=" * 80)
print("DRIVER'S LICENSE PATTERN COMPARISON")
print("=" * 80)

# Compare DL patterns
missing_states = []
mismatched_states = []
good_states = []

for state, ref_pattern in state_dl_reference.items():
    rule_id = f"PII-DL-{state}-1.0"
    rule = next((r for r in current_rules if r.get('id') == rule_id), None)
    
    if not rule:
        missing_states.append(state)
    else:
        current_pattern = rule.get('pattern', '')
        # Remove word boundaries for comparison
        current_clean = current_pattern.replace(r'\b', '').replace('\\b', '')
        ref_clean = ref_pattern.replace('^', '').replace('$', '')
        
        if current_clean != ref_clean:
            mismatched_states.append({
                'state': state,
                'current': current_pattern,
                'reference': ref_pattern
            })
        else:
            good_states.append(state)

print(f"\n✅ MATCHING: {len(good_states)} states")
print(f"❌ MISSING: {len(missing_states)} states")
if missing_states:
    print(f"   States: {', '.join(missing_states)}")

print(f"⚠️  MISMATCHED: {len(mismatched_states)} states")
if mismatched_states:
    for m in mismatched_states[:5]:
        print(f"\n   {m['state']}:")
        print(f"     Current:   {m['current'][:70]}")
        print(f"     Reference: {m['reference'][:70]}")
    if len(mismatched_states) > 5:
        print(f"   ... and {len(mismatched_states)-5} more")

print("\n" + "=" * 80)
print("FEDERAL ID COMPARISON")
print("=" * 80)

federal_status = []
for name, spec in federal_id_reference.items():
    # Search for matching rule
    found = False
    for rule in current_rules:
        rule_id = rule.get('id', '').lower()
        title = rule.get('title', '').lower()
        pattern = rule.get('pattern', '')
        
        # Fuzzy match
        if name.lower() in rule_id or name.lower() in title:
            found = True
            # Check pattern match (rough comparison)
            ref_pattern = spec['regex'].replace('^', '').replace('$', '')
            if ref_pattern in pattern or pattern.replace(r'\b', '').replace('\\b', '') == ref_pattern:
                federal_status.append(f"✅ {name}: Found and pattern matches")
            else:
                federal_status.append(f"⚠️  {name}: Found but pattern differs")
                federal_status.append(f"     Current: {pattern[:60]}")
                federal_status.append(f"     Reference: {spec['regex']}")
            break
    
    if not found:
        federal_status.append(f"❌ {name}: NOT FOUND - should add")
        federal_status.append(f"     Pattern: {spec['regex']}")

for status in federal_status:
    print(status)

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

if mismatched_states:
    print(f"\n1. UPDATE {len(mismatched_states)} driver's license patterns to match reference")
    
if missing_states:
    print(f"\n2. ADD {len(missing_states)} missing state DL rules")

missing_federal = [s for s in federal_status if 'NOT FOUND' in s]
if missing_federal:
    print(f"\n3. ADD {len(missing_federal)//2} missing federal ID rules:")
    for mf in missing_federal:
        if 'NOT FOUND' in mf:
            print(f"   • {mf.replace('❌ ', '').replace(': NOT FOUND - should add', '')}")

print("\nNext step: Run update script to apply changes")
