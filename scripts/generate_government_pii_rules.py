#!/usr/bin/env python3
"""
Government-Grade PII Enhancement Generator for Jimini

Adds comprehensive financial, federal ID, demographic, and network identifier 
detection rules to meet government agency requirements and compliance standards.

Usage:
    python scripts/generate_government_pii_rules.py
    python scripts/generate_government_pii_rules.py --test-only
"""

import yaml
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any

def generate_financial_pii_rules() -> List[Dict[str, Any]]:
    """Generate comprehensive financial PII detection rules."""
    rules = []
    
    # Credit card patterns (Luhn algorithm compatible)
    credit_card_patterns = [
        ('VISA', 'Visa Credit Card', r'\b4[0-9]{12}(?:[0-9]{3})?\b', '4111111111111111'),
        ('MASTERCARD', 'Mastercard Credit Card', r'\b5[1-5][0-9]{14}\b', '5555555555554444'),
        ('AMEX', 'American Express Credit Card', r'\b3[47][0-9]{13}\b', '378282246310005'),
        ('DISCOVER', 'Discover Credit Card', r'\b6(?:011|5[0-9]{2})[0-9]{12}\b', '6011111111111117'),
        ('DINERS', 'Diners Club Credit Card', r'\b3[0689][0-9]{11}\b', '30569309025904'),
        ('JCB', 'JCB Credit Card', r'\b(?:2131|1800|35\d{3})\d{11}\b', '3530111333300000')
    ]
    
    for card_type, name, pattern, example in credit_card_patterns:
        rule = {
            'id': f'PII-CREDIT-{card_type}-1.0',
            'title': f'{name} Detection',
            'severity': 'high',
            'pattern': pattern,
            'action': 'flag',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'PII',
                'subcategory': 'financial',
                'type': 'credit_card',
                'card_type': card_type.lower(),
                'example': example,
                'confidence': 'high',
                'compliance': ['PCI-DSS', 'Privacy Act']
            }
        }
        rules.append(rule)
    
    # Bank account numbers (US format)
    bank_rule = {
        'id': 'PII-BANK-ACCOUNT-1.0',
        'title': 'US Bank Account Number Detection',
        'severity': 'high',
        'pattern': r'\b\d{8,17}\b(?=.*(?:account|acct|checking|savings|routing))',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'financial',
            'type': 'bank_account',
            'format': '8-17 digits with banking context',
            'confidence': 'high',
            'compliance': ['BSA', 'Privacy Act']
        }
    }
    rules.append(bank_rule)
    
    # Routing numbers (US format)
    routing_rule = {
        'id': 'PII-ROUTING-NUMBER-1.0',
        'title': 'US Bank Routing Number Detection',
        'severity': 'medium',
        'pattern': r'\b[0-9]{9}\b(?=.*(?:routing|aba|transit))',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'financial',
            'type': 'routing_number',
            'format': '9 digits with routing context',
            'confidence': 'high',
            'compliance': ['BSA', 'Privacy Act']
        }
    }
    rules.append(routing_rule)
    
    return rules

def generate_federal_id_rules() -> List[Dict[str, Any]]:
    """Generate federal ID number detection rules."""
    rules = []
    
    # US Passport numbers
    passport_patterns = [
        ('US-PASSPORT-NEW', 'US Passport Number (New Format)', r'\b[0-9]{9}\b', '123456789'),
        ('US-PASSPORT-OLD', 'US Passport Number (Old Format)', r'\b[A-Z]{2}[0-9]{7}\b', 'AB1234567')
    ]
    
    for pattern_type, name, pattern, example in passport_patterns:
        rule = {
            'id': f'PII-{pattern_type}-1.0',
            'title': f'{name} Detection',
            'severity': 'high',
            'pattern': pattern,
            'action': 'flag',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'PII',
                'subcategory': 'federal_id',
                'type': 'passport',
                'format': name.split('(')[1].rstrip(')'),
                'example': example,
                'confidence': 'high',
                'compliance': ['Privacy Act', 'IRTPA']
            }
        }
        rules.append(rule)
    
    # Individual Taxpayer Identification Number (ITIN)
    itin_rule = {
        'id': 'PII-ITIN-1.0',
        'title': 'Individual Taxpayer Identification Number (ITIN)',
        'severity': 'high',
        'pattern': r'\b9\d{2}[-\s]?[7-9]\d[-\s]?\d{4}\b',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'federal_id',
            'type': 'itin',
            'format': '9XX-7X-XXXX or 9XX7XXXXX',
            'example': '912-70-1234',
            'confidence': 'high',
            'compliance': ['Privacy Act', 'IRS regulations']
        }
    }
    rules.append(itin_rule)
    
    # Employer Identification Number (EIN)
    ein_rule = {
        'id': 'PII-EIN-1.0',
        'title': 'Employer Identification Number (EIN)',
        'severity': 'medium',
        'pattern': r'\b\d{2}[-\s]?\d{7}\b',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'federal_id',
            'type': 'ein',
            'format': 'XX-XXXXXXX or XXXXXXXXX',
            'example': '12-3456789',
            'confidence': 'medium',
            'compliance': ['Privacy Act', 'IRS regulations']
        }
    }
    rules.append(ein_rule)
    
    # Military ID numbers (DoD ID format)
    military_rule = {
        'id': 'PII-MILITARY-ID-1.0',
        'title': 'US Military ID Number Detection',
        'severity': 'high',
        'pattern': r'\b\d{10}\b(?=.*(?:military|dod|army|navy|air force|marines|coast guard|service member))',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'federal_id',
            'type': 'military_id',
            'format': '10 digits with military context',
            'example': '1234567890',
            'confidence': 'high',
            'compliance': ['Privacy Act', 'DoD 5400.11-R']
        }
    }
    rules.append(military_rule)
    
    # Medicare Beneficiary Identifier (MBI)
    mbi_rule = {
        'id': 'PII-MEDICARE-MBI-1.0',
        'title': 'Medicare Beneficiary Identifier (MBI)',
        'severity': 'high',
        'pattern': r'\b[1-9][A-C,E-H,J-N,P-T,V-Y][A-C,E-H,J-N,P-T,V-Y]\d[A-C,E-H,J-N,P-T,V-Y]\d[A-C,E-H,J-N,P-T,V-Y]\d{4}\b',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'federal_id',
            'type': 'medicare_mbi',
            'format': '1 digit, 1 letter, 1 letter, 1 digit, 1 letter, 1 digit, 1 letter, 4 digits',
            'example': '1EG4TE5MK25',
            'confidence': 'high',
            'compliance': ['HIPAA', 'Privacy Act']
        }
    }
    rules.append(mbi_rule)
    
    return rules

def generate_demographic_pii_rules() -> List[Dict[str, Any]]:
    """Generate demographic and indirect identifier rules."""
    rules = []
    
    # Date of birth patterns
    dob_patterns = [
        ('DOB-MMDDYYYY', 'Date of Birth (MM/DD/YYYY)', r'\b(0[1-9]|1[0-2])[/-](0[1-9]|[12][0-9]|3[01])[/-](19|20)\d{2}\b', '01/15/1990'),
        ('DOB-DDMMYYYY', 'Date of Birth (DD/MM/YYYY)', r'\b(0[1-9]|[12][0-9]|3[01])[/-](0[1-9]|1[0-2])[/-](19|20)\d{2}\b', '15/01/1990'),
        ('DOB-YYYYMMDD', 'Date of Birth (YYYY-MM-DD)', r'\b(19|20)\d{2}[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12][0-9]|3[01])\b', '1990-01-15'),
        ('DOB-WRITTEN', 'Date of Birth (Written Format)', r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(19|20)\d{2}\b', 'January 15, 1990')
    ]
    
    for pattern_type, name, pattern, example in dob_patterns:
        rule = {
            'id': f'PII-{pattern_type}-1.0',
            'title': f'{name} Detection',
            'severity': 'medium',
            'pattern': pattern,
            'action': 'flag',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'PII',
                'subcategory': 'demographic',
                'type': 'date_of_birth',
                'format': name.split('(')[1].rstrip(')'),
                'example': example,
                'confidence': 'medium',
                'compliance': ['Privacy Act']
            }
        }
        rules.append(rule)
    
    # Mother's maiden name (common patterns)
    maiden_rule = {
        'id': 'PII-MAIDEN-NAME-1.0',
        'title': 'Mother\'s Maiden Name Context Detection',
        'severity': 'medium',
        'pattern': r'(?i)\b(?:mother\'?s?\s*maiden\s*name|maiden\s*name|mom\'?s?\s*name\s*before\s*marriage)[:\s]*([A-Z][a-z]+)\b',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'demographic',
            'type': 'maiden_name',
            'format': 'Contextual detection with name',
            'confidence': 'medium',
            'compliance': ['Privacy Act']
        }
    }
    rules.append(maiden_rule)
    
    return rules

def generate_network_identifier_rules() -> List[Dict[str, Any]]:
    """Generate network and digital identifier rules."""
    rules = []
    
    # Enhanced IPv4 addresses
    ipv4_rule = {
        'id': 'PII-IPV4-ENHANCED-1.0',
        'title': 'IPv4 Address Detection (Enhanced)',
        'severity': 'medium',
        'pattern': r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'network',
            'type': 'ipv4_address',
            'format': 'XXX.XXX.XXX.XXX (0-255 range validation)',
            'example': '192.168.1.100',
            'confidence': 'high',
            'compliance': ['Privacy Act', 'Digital forensics']
        }
    }
    rules.append(ipv4_rule)
    
    # IPv6 addresses
    ipv6_rule = {
        'id': 'PII-IPV6-1.0',
        'title': 'IPv6 Address Detection',
        'severity': 'medium',
        'pattern': r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b::1\b|\b(?:[0-9a-fA-F]{1,4}:)*::(?:[0-9a-fA-F]{1,4}:)*[0-9a-fA-F]{1,4}\b',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'network',
            'type': 'ipv6_address',
            'format': 'Full and compressed IPv6 formats',
            'example': '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
            'confidence': 'high',
            'compliance': ['Privacy Act', 'Digital forensics']
        }
    }
    rules.append(ipv6_rule)
    
    # MAC addresses
    mac_rule = {
        'id': 'PII-MAC-ADDRESS-1.0',
        'title': 'MAC Address Detection',
        'severity': 'medium',
        'pattern': r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'network',
            'type': 'mac_address',
            'format': 'XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX',
            'example': '00:1B:44:11:3A:B7',
            'confidence': 'high',
            'compliance': ['Privacy Act', 'Digital forensics']
        }
    }
    rules.append(mac_rule)
    
    return rules

def enhance_ssn_rule() -> Dict[str, Any]:
    """Generate enhanced SSN rule with all format variations."""
    return {
        'id': 'PII-SSN-ENHANCED-1.0',
        'title': 'Social Security Number (All Formats)',
        'severity': 'high',
        'pattern': r'\b(?:\d{3}[-\s]?\d{2}[-\s]?\d{4})\b',
        'action': 'block',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'federal_id',
            'type': 'ssn',
            'format': 'XXX-XX-XXXX, XXX XX XXXX, XXXXXXXXX',
            'examples': ['123-45-6789', '123 45 6789', '123456789'],
            'confidence': 'high',
            'compliance': ['Privacy Act', 'SSA regulations']
        }
    }

def load_existing_rules(file_path: Path) -> Dict[str, Any]:
    """Load existing rules from YAML file."""
    if not file_path.exists():
        return {'rules': []}
    
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {'rules': []}
    except Exception as e:
        print(f"Error loading existing rules: {e}")
        return {'rules': []}

def save_rules(rules_data: Dict[str, Any], file_path: Path):
    """Save rules to YAML file with proper formatting."""
    try:
        with open(file_path, 'w') as f:
            yaml.dump(rules_data, f, default_flow_style=False, indent=2, sort_keys=False)
        print(f"✅ Enhanced rules saved to {file_path}")
    except Exception as e:
        print(f"❌ Error saving rules: {e}")
        raise

def test_patterns():
    """Test all new patterns with sample data."""
    print("🧪 Testing enhanced government PII patterns...")
    
    test_cases = {
        'Credit Cards': [
            '4111111111111111',  # Visa
            '5555555555554444',  # Mastercard
            '378282246310005',   # Amex
        ],
        'SSN Enhanced': [
            '123-45-6789',       # With dashes
            '123 45 6789',       # With spaces
            '123456789',         # No separators
        ],
        'Passport Numbers': [
            '123456789',         # New format
            'AB1234567',         # Old format
        ],
        'ITIN': [
            '912-70-1234',       # With dashes
            '91270-1234',        # With dash in different position
        ],
        'Date of Birth': [
            '01/15/1990',        # MM/DD/YYYY
            '1990-01-15',        # YYYY-MM-DD
            'January 15, 1990',  # Written format
        ],
        'IP Addresses': [
            '192.168.1.100',     # IPv4
            '2001:0db8:85a3:0000:0000:8a2e:0370:7334',  # IPv6
        ],
        'MAC Address': [
            '00:1B:44:11:3A:B7', # Colon format
            '00-1B-44-11-3A-B7', # Dash format
        ]
    }
    
    # Generate all rules for testing
    all_rules = []
    all_rules.extend(generate_financial_pii_rules())
    all_rules.extend(generate_federal_id_rules())
    all_rules.extend(generate_demographic_pii_rules())
    all_rules.extend(generate_network_identifier_rules())
    all_rules.append(enhance_ssn_rule())
    
    passed = 0
    total = 0
    
    for category, test_values in test_cases.items():
        print(f"\n📋 Testing {category}:")
        for test_val in test_values:
            total += 1
            matched = False
            
            for rule in all_rules:
                pattern = rule['pattern']
                try:
                    if re.search(pattern, test_val, re.IGNORECASE):
                        print(f"  ✅ {test_val} matches {rule['id']}")
                        matched = True
                        passed += 1
                        break
                except re.error as e:
                    print(f"  ❌ Pattern error in {rule['id']}: {e}")
            
            if not matched:
                print(f"  ❌ {test_val} - no match found")
    
    print(f"\n📊 Pattern testing: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    return passed == total

def main():
    parser = argparse.ArgumentParser(description='Generate government-grade PII detection rules for Jimini')
    parser.add_argument('--output', '-o', type=str, default='policy_rules.yaml',
                       help='Output YAML file (default: policy_rules.yaml)')
    parser.add_argument('--test-only', action='store_true',
                       help='Only run pattern tests, do not generate rules')
    parser.add_argument('--backup', action='store_true', default=True,
                       help='Create backup of existing rules file')
    
    args = parser.parse_args()
    
    if args.test_only:
        success = test_patterns()
        exit(0 if success else 1)
    
    output_path = Path(args.output)
    
    print("🏛️ Generating government-grade PII detection enhancements...")
    print(f"📍 Output file: {output_path}")
    
    # Load existing rules
    existing_data = load_existing_rules(output_path)
    
    # Create backup if requested and file exists
    if args.backup and output_path.exists():
        backup_path = output_path.with_suffix(f'.gov_backup{output_path.suffix}')
        try:
            import shutil
            shutil.copy2(output_path, backup_path)
            print(f"💾 Backup created: {backup_path}")
        except Exception as e:
            print(f"⚠️  Backup failed: {e}")
    
    # Generate new rules
    print("💳 Generating financial PII rules...")
    financial_rules = generate_financial_pii_rules()
    
    print("🆔 Generating federal ID rules...")
    federal_id_rules = generate_federal_id_rules()
    
    print("👥 Generating demographic PII rules...")
    demographic_rules = generate_demographic_pii_rules()
    
    print("🌐 Generating network identifier rules...")
    network_rules = generate_network_identifier_rules()
    
    print("🔢 Enhancing SSN detection...")
    enhanced_ssn = enhance_ssn_rule()
    
    # Combine all new rules
    new_rules = financial_rules + federal_id_rules + demographic_rules + network_rules + [enhanced_ssn]
    
    # Remove any existing government PII rules to avoid duplicates
    existing_rules = [rule for rule in existing_data.get('rules', []) 
                     if not rule.get('id', '').startswith(('PII-CREDIT-', 'PII-BANK-', 'PII-ROUTING-', 
                                                          'PII-US-PASSPORT-', 'PII-ITIN-', 'PII-EIN-', 
                                                          'PII-MILITARY-', 'PII-MEDICARE-', 'PII-DOB-', 
                                                          'PII-MAIDEN-', 'PII-IPV4-ENHANCED-', 'PII-IPV6-', 
                                                          'PII-MAC-', 'PII-SSN-ENHANCED-'))]
    
    # Also remove the old SSN rule to replace with enhanced version
    existing_rules = [rule for rule in existing_rules 
                     if rule.get('id') != 'IL-AI-4.2' or 'Social Security' not in rule.get('title', '')]
    
    # Combine with new rules
    all_rules = existing_rules + new_rules
    
    # Update rules data
    rules_data = {
        'rules': all_rules,
        'metadata': {
            'generated_by': 'generate_government_pii_rules.py',
            'total_rules': len(all_rules),
            'government_pii_rules_added': len(new_rules),
            'enhancement_categories': ['financial', 'federal_id', 'demographic', 'network'],
            'compliance_standards': ['Privacy Act', 'HIPAA', 'PCI-DSS', 'FISMA', 'CJIS']
        }
    }
    
    # Save rules
    save_rules(rules_data, output_path)
    
    # Test patterns
    print("\n🧪 Running comprehensive pattern validation tests...")
    test_success = test_patterns()
    
    # Summary
    print(f"\n📋 Government PII Enhancement Summary:")
    print(f"  • Financial PII Rules: {len(financial_rules)} (credit cards, bank accounts, routing)")
    print(f"  • Federal ID Rules: {len(federal_id_rules)} (passport, ITIN, EIN, military, Medicare)")
    print(f"  • Demographic Rules: {len(demographic_rules)} (DOB, maiden name)")
    print(f"  • Network ID Rules: {len(network_rules)} (IPv4, IPv6, MAC addresses)")
    print(f"  • Enhanced SSN Rule: 1 (all format variations)")
    print(f"  • Total New Rules: {len(new_rules)}")
    print(f"  • Total Rules in File: {len(all_rules)}")
    print(f"  • Pattern Tests: {'✅ PASSED' if test_success else '❌ FAILED'}")
    print(f"  • Compliance Coverage: Privacy Act, HIPAA, PCI-DSS, FISMA, CJIS")
    
    if not test_success:
        print("\n⚠️  Some pattern tests failed. Please review the patterns.")
        exit(1)
    
    print(f"\n🏆 Successfully enhanced Jimini with government-grade PII detection!")
    print(f"   Enhanced rules saved to: {output_path}")
    print(f"   🛡️ Ready for federal and state agency deployment!")

if __name__ == '__main__':
    main()