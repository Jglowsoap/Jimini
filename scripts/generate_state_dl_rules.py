#!/usr/bin/env python3
"""
Jimini State-Specific Driver's License Pattern Generator

Generates YAML rules for driver's license detection across all 50 US states + DC
based on actual DMV documentation and format specifications.

Usage:
    python scripts/generate_state_dl_rules.py
    python scripts/generate_state_dl_rules.py --output custom_rules.yaml
    python scripts/generate_state_dl_rules.py --test-only
"""

import yaml
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Research-based state driver's license patterns from DMV documentation
STATE_DL_PATTERNS = {
    # Format: (state, description, regex_pattern, example)
    'AL': ('Alabama', '1-8 digits', r'\b\d{1,8}\b', '1234567'),
    'AK': ('Alaska', '1-7 digits', r'\b\d{1,7}\b', '1234567'),
    'AZ': ('Arizona', '1 letter + 8 digits OR 2 letters + 2-5 digits OR 9 digits', r'\b[A-Z]\d{8}\b|\b[A-Z]{2}\d{2,5}\b|\b\d{9}\b', 'A12345678'),
    'AR': ('Arkansas', '4-9 digits', r'\b\d{4,9}\b', '123456789'),
    'CA': ('California', '1 letter + 7 digits', r'\b[A-Z]\d{7}\b', 'A1234567'),
    'CO': ('Colorado', '9 digits OR 1-2 letters + 1-6 digits', r'\b\d{9}\b|\b[A-Z]{1,2}\d{1,6}\b', '123456789'),
    'CT': ('Connecticut', '9 digits', r'\b\d{9}\b', '123456789'),
    'DE': ('Delaware', '1-7 digits', r'\b\d{1,7}\b', '1234567'),
    'DC': ('District of Columbia', '7 digits OR 1-3 letters + 3-7 digits', r'\b\d{7}\b|\b[A-Z]{1,3}\d{3,7}\b', '1234567'),
    'FL': ('Florida', '1 letter + 12 digits', r'\b[A-Z]\d{12}\b', 'A123456789012'),
    'GA': ('Georgia', '7-9 digits', r'\b\d{7,9}\b', '123456789'),
    'HI': ('Hawaii', '1 letter + 8 digits OR 9 digits', r'\b[A-Z]\d{8}\b|\b\d{9}\b', 'H12345678'),
    'ID': ('Idaho', '2 letters + 6 digits + 1 letter OR 9 digits', r'\b[A-Z]{2}\d{6}[A-Z]\b|\b\d{9}\b', 'AB123456C'),
    'IL': ('Illinois', '1 letter + 11 digits (DL) OR 11 digits + 1 letter (ID)', r'\b[A-Z]\d{11}\b|\b\d{11}[A-Z]\b', 'A12345678901'),
    'IN': ('Indiana', '1 letter + 9 digits OR 10 digits', r'\b[A-Z]\d{9}\b|\b\d{10}\b', 'A123456789'),
    'IA': ('Iowa', '9 digits OR 3 digits + 2 letters + 4 digits', r'\b\d{9}\b|\b\d{3}[A-Z]{2}\d{4}\b', '123456789'),
    'KS': ('Kansas', '1 letter + 8 digits OR 9 digits', r'\b[A-Z]\d{8}\b|\b\d{9}\b', 'K12345678'),
    'KY': ('Kentucky', '1 letter + 8 digits OR 9 digits', r'\b[A-Z]\d{8}\b|\b\d{9}\b', 'K12345678'),
    'LA': ('Louisiana', '1-9 digits', r'\b\d{1,9}\b', '123456789'),
    'ME': ('Maine', '7 digits OR 7 digits + 1 letter', r'\b\d{7}[A-Z]?\b', '1234567'),
    'MD': ('Maryland', '1 letter + 12 digits', r'\b[A-Z]\d{12}\b', 'M123456789012'),
    'MA': ('Massachusetts', '1 letter + 8 digits OR 9 digits', r'\b[A-Z]\d{8}\b|\b\d{9}\b', 'S12345678'),
    'MI': ('Michigan', '1 letter + 12 digits OR 1 letter + 10 digits', r'\b[A-Z]\d{10,12}\b', 'A123456789012'),
    'MN': ('Minnesota', '1 letter + 12 digits', r'\b[A-Z]\d{12}\b', 'A123456789012'),
    'MS': ('Mississippi', '9 digits', r'\b\d{9}\b', '123456789'),
    'MO': ('Missouri', '1 letter + 5-9 digits OR 1 letter + 6 digits + R OR 8-9 digits', r'\b[A-Z]\d{5,9}\b|\b[A-Z]\d{6}R\b|\b\d{8,9}\b', 'A123456789'),
    'MT': ('Montana', '13 digits OR 9 digits + 3 letters OR 14 digits', r'\b\d{13}\b|\b\d{9}[A-Z]{3}\b|\b\d{14}\b', '1234567890123'),
    'NE': ('Nebraska', '1 letter + 3-8 digits', r'\b[A-Z]\d{3,8}\b', 'A12345678'),
    'NV': ('Nevada', '4 digits + 12 digits OR 12 digits', r'\b\d{4}\d{12}\b|\b\d{12}\b', '123456789012'),
    'NH': ('New Hampshire', '2 digits + 3 letters + 5 digits', r'\b\d{2}[A-Z]{3}\d{5}\b', '12ABC34567'),
    'NJ': ('New Jersey', '1 letter + 14 digits', r'\b[A-Z]\d{14}\b', 'A12345678901234'),
    'NM': ('New Mexico', '8-9 digits', r'\b\d{8,9}\b', '123456789'),
    'NY': ('New York', '1 letter + 7 digits OR 1 letter + 18 digits OR 8-9 digits OR 16 digits', r'\b[A-Z]\d{7}\b|\b[A-Z]\d{18}\b|\b\d{8,9}\b|\b\d{16}\b', 'A1234567'),
    'NC': ('North Carolina', '1-12 digits', r'\b\d{1,12}\b', '123456789012'),
    'ND': ('North Dakota', '3 letters + 6 digits OR 9 digits', r'\b[A-Z]{3}\d{6}\b|\b\d{9}\b', 'ABC123456'),
    'OH': ('Ohio', '1 letter + 4-8 digits OR 2 letters + 3-7 digits OR 8 digits', r'\b[A-Z]\d{4,8}\b|\b[A-Z]{2}\d{3,7}\b|\b\d{8}\b', 'A12345678'),
    'OK': ('Oklahoma', '1 letter + 9 digits OR 9 digits', r'\b[A-Z]\d{9}\b|\b\d{9}\b', 'A123456789'),
    'OR': ('Oregon', '1-9 digits', r'\b\d{1,9}\b', '123456789'),
    'PA': ('Pennsylvania', '8 digits', r'\b\d{8}\b', '12345678'),
    'RI': ('Rhode Island', '1 letter + 6 digits OR 7 digits', r'\b[A-Z]\d{6}\b|\b\d{7}\b', 'A123456'),
    'SC': ('South Carolina', '5-11 digits', r'\b\d{5,11}\b', '12345678901'),
    'SD': ('South Dakota', '6-10 digits OR 12 digits', r'\b\d{6,10}\b|\b\d{12}\b', '123456789'),
    'TN': ('Tennessee', '7-9 digits', r'\b\d{7,9}\b', '123456789'),
    'TX': ('Texas', '7-8 digits', r'\b\d{7,8}\b', '12345678'),
    'UT': ('Utah', '4-10 digits', r'\b\d{4,10}\b', '1234567890'),
    'VT': ('Vermont', '8 digits OR 7 digits + A', r'\b\d{8}\b|\b\d{7}A\b', '12345678'),
    'VA': ('Virginia', '1 letter + 8 digits OR 9 digits', r'\b[A-Z]\d{8}\b|\b\d{9}\b', 'A12345678'),
    'WA': ('Washington', '1-12 letters/digits with at least 1 letter OR WDL + 9 digits', r'\b(?=.*[A-Z])[A-Z0-9]{1,12}\b|\bWDL\d{9}\b', 'ABC123DEF456'),
    'WV': ('West Virginia', '1-2 letters + 5-6 digits OR 7 digits', r'\b[A-Z]{1,2}\d{5,6}\b|\b\d{7}\b', 'A123456'),
    'WI': ('Wisconsin', '1 letter + 13 digits', r'\b[A-Z]\d{13}\b', 'A1234567890123'),
    'WY': ('Wyoming', '9-10 digits', r'\b\d{9,10}\b', '1234567890'),
}

# Additional license plate patterns for comprehensive vehicle identification
STATE_LICENSE_PLATE_PATTERNS = {
    'STANDARD': ('Standard US License Plates', '3 letters + 3-4 digits OR 3-4 digits + 3 letters OR mixed patterns', 
                 r'\b[A-Z]{3}[-\s]?\d{3,4}\b|\b\d{3,4}[-\s]?[A-Z]{3}\b|\b[A-Z]{2,3}[-\s]?\d{2,4}[-\s]?[A-Z]?\b', 'ABC1234'),
    'SPECIALTY': ('Specialty/Vanity Plates', 'Custom alphanumeric combinations 2-8 characters', 
                  r'\b(?=.*[A-Z])(?=.*\d)[A-Z0-9]{2,8}\b', 'CUSTOM1'),
    'COMMERCIAL': ('Commercial Vehicle Plates', 'Commercial format patterns', 
                   r'\bT\d{6}\b|\bC\d{5,7}\b|\bCOM\d{4}\b', 'T123456'),
}

def generate_state_dl_rules() -> List[Dict[str, Any]]:
    """Generate YAML rule entries for all state driver's license patterns."""
    rules = []
    
    # Generate individual state rules
    for state_code, (state_name, description, pattern, example) in STATE_DL_PATTERNS.items():
        rule = {
            'id': f'PII-DL-{state_code}-1.0',
            'title': f'{state_name} Driver\'s License Detection',
            'severity': 'medium',
            'pattern': pattern,
            'action': 'flag',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'PII',
                'subcategory': 'drivers_license',
                'state': state_code,
                'format': description,
                'example': example,
                'confidence': 'high'
            }
        }
        rules.append(rule)
    
    # Add comprehensive US driver's license rule
    all_patterns = [pattern for _, (_, _, pattern, _) in STATE_DL_PATTERNS.items()]
    combined_pattern = '|'.join(f'({pattern})' for pattern in all_patterns)
    
    comprehensive_rule = {
        'id': 'PII-DL-US-1.0',
        'title': 'US Driver\'s License Comprehensive Detection',
        'severity': 'medium',
        'pattern': combined_pattern,
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'drivers_license',
            'scope': 'all_states',
            'confidence': 'high',
            'states_covered': list(STATE_DL_PATTERNS.keys())
        }
    }
    rules.append(comprehensive_rule)
    
    return rules

def generate_license_plate_rules() -> List[Dict[str, Any]]:
    """Generate license plate detection rules."""
    rules = []
    
    for plate_type, (name, description, pattern, example) in STATE_LICENSE_PLATE_PATTERNS.items():
        rule = {
            'id': f'PII-LP-{plate_type}-1.0',
            'title': f'{name} Detection',
            'severity': 'medium',
            'pattern': pattern,
            'action': 'flag',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'PII',
                'subcategory': 'license_plate',
                'type': plate_type.lower(),
                'format': description,
                'example': example,
                'confidence': 'medium'
            }
        }
        rules.append(rule)
    
    return rules

def generate_address_rules() -> List[Dict[str, Any]]:
    """Generate US address detection rules."""
    rules = []
    
    # Street address pattern
    street_rule = {
        'id': 'PII-ADDR-STREET-1.0',
        'title': 'US Street Address Detection',
        'severity': 'medium',
        'pattern': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Circle|Cir|Court|Ct|Place|Pl|Way)\b',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'address',
            'type': 'street_address',
            'confidence': 'high'
        }
    }
    rules.append(street_rule)
    
    # ZIP code pattern
    zip_rule = {
        'id': 'PII-ADDR-ZIP-1.0',
        'title': 'US ZIP Code Detection',
        'severity': 'medium',
        'pattern': r'\b\d{5}(?:-\d{4})?\b',
        'action': 'flag',
        'applies_to': ['request', 'response'],
        'endpoints': ['*'],
        'metadata': {
            'category': 'PII',
            'subcategory': 'address',
            'type': 'zip_code',
            'confidence': 'high'
        }
    }
    rules.append(zip_rule)
    
    return rules

def generate_phone_rules() -> List[Dict[str, Any]]:
    """Generate comprehensive phone number detection rules."""
    rules = []
    
    # US phone number patterns
    phone_patterns = [
        (r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}', 'US phone with parentheses', '(555) 123-4567'),
        (r'\d{3}[-.\s]\d{3}[-.\s]\d{4}', 'US phone with separators', '555-123-4567'),
        (r'\b\d{10}\b', 'US phone 10 digits', '5551234567'),
        (r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', 'US phone with country code', '+1-555-123-4567'),
    ]
    
    for i, (pattern, description, example) in enumerate(phone_patterns, 1):
        rule = {
            'id': f'PII-PHONE-US-{i}.0',
            'title': f'US Phone Number Detection ({description})',
            'severity': 'medium',
            'pattern': pattern,
            'action': 'flag',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'PII',
                'subcategory': 'phone_number',
                'format': description,
                'example': example,
                'confidence': 'high'
            }
        }
        rules.append(rule)
    
    return rules

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
        print(f"✅ Rules saved to {file_path}")
    except Exception as e:
        print(f"❌ Error saving rules: {e}")
        raise

def test_patterns():
    """Test all patterns with sample data."""
    print("🧪 Testing state driver's license patterns...")
    
    test_cases = {
        'IL': ['A12345678901', 'B98765432100', '12345678901A', '98765432100B'],
        'CA': ['A1234567', 'B9876543'],
        'FL': ['A123456789012', 'B987654321098'],
        'TX': ['1234567', '12345678'],
        'NY': ['A1234567', '12345678', '123456789'],
    }
    
    passed = 0
    total = 0
    
    for state, test_values in test_cases.items():
        if state not in STATE_DL_PATTERNS:
            continue
            
        pattern = STATE_DL_PATTERNS[state][2]
        compiled_pattern = re.compile(pattern)
        
        for test_val in test_values:
            total += 1
            if compiled_pattern.search(test_val):
                print(f"  ✅ {state}: {test_val} matches")
                passed += 1
            else:
                print(f"  ❌ {state}: {test_val} does not match")
    
    print(f"\n📊 Pattern testing: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    return passed == total

def main():
    parser = argparse.ArgumentParser(description='Generate state-specific PII detection rules for Jimini')
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
    
    print("🚀 Generating comprehensive PII detection rules...")
    print(f"📍 Output file: {output_path}")
    
    # Load existing rules
    existing_data = load_existing_rules(output_path)
    
    # Create backup if requested and file exists
    if args.backup and output_path.exists():
        backup_path = output_path.with_suffix(f'.backup{output_path.suffix}')
        try:
            import shutil
            shutil.copy2(output_path, backup_path)
            print(f"💾 Backup created: {backup_path}")
        except Exception as e:
            print(f"⚠️  Backup failed: {e}")
    
    # Generate new rules
    print("🏛️  Generating state driver's license rules...")
    dl_rules = generate_state_dl_rules()
    
    print("🚗 Generating license plate rules...")
    lp_rules = generate_license_plate_rules()
    
    print("🏠 Generating address rules...")
    addr_rules = generate_address_rules()
    
    print("📞 Generating phone number rules...")
    phone_rules = generate_phone_rules()
    
    # Combine all new rules
    new_rules = dl_rules + lp_rules + addr_rules + phone_rules
    
    # Remove any existing PII rules to avoid duplicates
    existing_rules = [rule for rule in existing_data.get('rules', []) 
                     if not rule.get('id', '').startswith(('PII-DL-', 'PII-LP-', 'PII-ADDR-', 'PII-PHONE-'))]
    
    # Combine with new rules
    all_rules = existing_rules + new_rules
    
    # Update rules data
    rules_data = {
        'rules': all_rules,
        'metadata': {
            'generated_by': 'generate_state_dl_rules.py',
            'total_rules': len(all_rules),
            'pii_rules_added': len(new_rules),
            'states_covered': len(STATE_DL_PATTERNS),
        }
    }
    
    # Save rules
    save_rules(rules_data, output_path)
    
    # Test patterns
    print("\n🧪 Running pattern validation tests...")
    test_success = test_patterns()
    
    # Summary
    print(f"\n📋 Generation Summary:")
    print(f"  • Driver's License Rules: {len(dl_rules)} (all 50 states + DC)")
    print(f"  • License Plate Rules: {len(lp_rules)}")
    print(f"  • Address Rules: {len(addr_rules)}")
    print(f"  • Phone Number Rules: {len(phone_rules)}")
    print(f"  • Total New PII Rules: {len(new_rules)}")
    print(f"  • Total Rules in File: {len(all_rules)}")
    print(f"  • Pattern Tests: {'✅ PASSED' if test_success else '❌ FAILED'}")
    
    if not test_success:
        print("\n⚠️  Some pattern tests failed. Please review the patterns.")
        exit(1)
    
    print(f"\n🎉 Successfully generated comprehensive PII detection rules!")
    print(f"   Rules saved to: {output_path}")

if __name__ == '__main__':
    main()
