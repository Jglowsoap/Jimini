#!/usr/bin/env python3
"""
Cleanup and reorganize policy_rules.yaml actions:
- BLOCK: Critical secrets (SSN, credit cards, API keys, passwords, tokens, driver's licenses if high risk)
- REDACT: Sensitive PII (emails, phones, IP/MAC/network, driver's licenses, addresses)
- FLAG: Content quality only (hallucinations, toxicity - not for data protection)
- ALLOW: Clean content

Also removes duplicate rules.
"""

import yaml
from collections import defaultdict

def main():
    with open('policy_rules.yaml', 'r') as f:
        rules = yaml.safe_load(f)
    
    print(f"Starting with {len(rules)} rules")
    
    # Track duplicates by category
    duplicates_to_remove = []
    rules_by_purpose = defaultdict(list)
    
    for i, rule in enumerate(rules):
        rid = rule.get('id', '')
        title = rule.get('title', '').lower()
        action = rule.get('action', '')
        
        # Identify duplicates to remove (keep the better one)
        if rid == 'EMAIL-1.0' and action == 'flag':
            duplicates_to_remove.append(i)
            print(f"  Removing duplicate: {rid} (keeping PII-EMAIL-1.0 with redact)")
        elif rid == 'HIPAA-PHI-EMAIL-1.0' and action == 'flag':
            duplicates_to_remove.append(i)
            print(f"  Removing duplicate: {rid} (covered by PII-EMAIL-1.0)")
        elif rid.startswith('PII-CREDIT-') and rid not in ['PII-CREDIT-CARD-1.0'] and action == 'flag':
            # Remove individual card type flags (Visa, MC, etc.) - generic block covers them
            duplicates_to_remove.append(i)
            print(f"  Removing duplicate: {rid} (covered by PII-CREDIT-CARD-1.0)")
        elif any(x in title for x in ['visa', 'mastercard', 'amex', 'discover']) and 'credit' in title and action == 'flag':
            duplicates_to_remove.append(i)
            print(f"  Removing duplicate: {rid} (covered by PII-CREDIT-CARD-1.0)")
    
    # Remove duplicates
    rules = [r for i, r in enumerate(rules) if i not in duplicates_to_remove]
    print(f"\nAfter removing duplicates: {len(rules)} rules")
    
    # Now update actions for remaining flagged rules
    changes = []
    for rule in rules:
        rid = rule.get('id', '')
        title = rule.get('title', '').lower()
        action = rule.get('action', '')
        
        if action != 'flag':
            continue
            
        new_action = None
        reason = ""
        
        # PII to REDACT
        if any(x in rid.lower() or x in title for x in [
            'ip-address', 'ipv4', 'ipv6', 'mac', 'phone', 'subnet', 'network',
            '-dl-', 'driver', 'license', 'plate', 'address', 'street', 'zip',
            'bank-account', 'routing-number'
        ]):
            new_action = 'redact'
            reason = "PII - should be masked"
        
        # Security to BLOCK
        elif any(x in rid.lower() or x in title for x in [
            'jwt', 'token', 'injection', 'bypass', 'biometric', 
            'export', 'compliance-bypass', 'override', 'ignore'
        ]):
            new_action = 'block'
            reason = "Security threat - must be blocked"
        
        # Content quality - keep as FLAG
        elif any(x in title for x in [
            'hallucination', 'toxic', 'offensive', 'confidence', 'slur'
        ]) or any(x in rid.lower() for x in ['halluc', 'toxic']):
            # Keep as flag
            reason = "Content quality - keeping as FLAG"
        else:
            reason = "NEEDS REVIEW - unclear category"
        
        if new_action and new_action != action:
            rule['action'] = new_action
            changes.append(f"  {rid}: flag → {new_action} ({reason})")
    
    print(f"\n=== ACTION CHANGES ({len(changes)}) ===")
    for change in changes[:20]:
        print(change)
    if len(changes) > 20:
        print(f"  ... and {len(changes)-20} more")
    
    # Count final distribution
    action_counts = defaultdict(int)
    for rule in rules:
        action_counts[rule.get('action', 'unknown')] += 1
    
    print(f"\n=== FINAL DISTRIBUTION ===")
    for action, count in sorted(action_counts.items()):
        print(f"  {action}: {count}")
    
    # Backup and save
    import shutil
    from datetime import datetime
    backup_name = f"policy_rules_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
    shutil.copy('policy_rules.yaml', backup_name)
    print(f"\n✅ Backed up to {backup_name}")
    
    with open('policy_rules.yaml', 'w') as f:
        yaml.dump(rules, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"✅ Updated policy_rules.yaml ({len(rules)} rules)")
    print(f"\nNext steps:")
    print(f"  1. Review changes: git diff policy_rules.yaml")
    print(f"  2. Test: jimini test --rules policy_rules.yaml --text 'test@example.com'")
    print(f"  3. Verify dashboard shows correct actions")

if __name__ == '__main__':
    main()
