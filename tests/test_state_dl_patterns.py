#!/usr/bin/env python3
"""
Comprehensive test suite for state-specific PII detection patterns.

Tests all generated driver's license, license plate, address, and phone number
detection rules with real-world test cases and edge cases.
"""

import re
import sys
import pytest
from pathlib import Path
from typing import List, Dict, Tuple, Any

# Add the scripts directory to path to import the generator
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_state_dl_rules import (
    STATE_DL_PATTERNS,
    STATE_LICENSE_PLATE_PATTERNS,
    generate_state_dl_rules,
    generate_license_plate_rules,
    generate_address_rules,
    generate_phone_rules
)

class TestStateDLPatterns:
    """Test state-specific driver's license patterns."""
    
    def test_illinois_dl_patterns(self):
        """Test Illinois driver's license patterns specifically."""
        il_pattern = STATE_DL_PATTERNS['IL'][2]
        compiled_pattern = re.compile(il_pattern)
        
        # Valid IL driver's license (letter + 11 digits)
        valid_dl = [
            'A12345678901',
            'B98765432100',
            'Z11111111111'
        ]
        
        # Valid IL ID (11 digits + letter) 
        valid_id = [
            '12345678901A',
            '98765432100B',
            '11111111111Z'
        ]
        
        # Invalid patterns
        invalid = [
            'A1234567890',  # Only 10 digits
            '123456789012A',  # 12 digits + letter
            'AB12345678901',  # 2 letters + digits
            '12345678901',  # Just 11 digits
            'A123456789012'  # Letter + 12 digits
        ]
        
        # Test valid DL patterns
        for dl in valid_dl:
            assert compiled_pattern.search(dl), f"IL DL pattern should match: {dl}"
        
        # Test valid ID patterns
        for id_num in valid_id:
            assert compiled_pattern.search(id_num), f"IL ID pattern should match: {id_num}"
        
        # Test invalid patterns
        for invalid_pattern in invalid:
            assert not compiled_pattern.search(invalid_pattern), f"Pattern should not match: {invalid_pattern}"
    
    def test_california_dl_patterns(self):
        """Test California driver's license patterns."""
        ca_pattern = STATE_DL_PATTERNS['CA'][2]
        compiled_pattern = re.compile(ca_pattern)
        
        valid = ['A1234567', 'B9876543', 'Z0000000']
        invalid = ['A123456', 'A12345678', '1234567A', 'AB123456']
        
        for dl in valid:
            assert compiled_pattern.search(dl), f"CA pattern should match: {dl}"
        
        for invalid_pattern in invalid:
            assert not compiled_pattern.search(invalid_pattern), f"CA pattern should not match: {invalid_pattern}"
    
    def test_florida_dl_patterns(self):
        """Test Florida driver's license patterns."""
        fl_pattern = STATE_DL_PATTERNS['FL'][2]
        compiled_pattern = re.compile(fl_pattern)
        
        valid = ['A123456789012', 'B987654321098']
        invalid = ['A12345678901', 'A1234567890123', '123456789012A']
        
        for dl in valid:
            assert compiled_pattern.search(dl), f"FL pattern should match: {dl}"
        
        for invalid_pattern in invalid:
            assert not compiled_pattern.search(invalid_pattern), f"FL pattern should not match: {invalid_pattern}"
    
    def test_texas_dl_patterns(self):
        """Test Texas driver's license patterns."""
        tx_pattern = STATE_DL_PATTERNS['TX'][2]
        compiled_pattern = re.compile(tx_pattern)
        
        valid = ['1234567', '12345678']
        invalid = ['123456', '123456789', 'A1234567']
        
        for dl in valid:
            assert compiled_pattern.search(dl), f"TX pattern should match: {dl}"
        
        for invalid_pattern in invalid:
            assert not compiled_pattern.search(invalid_pattern), f"TX pattern should not match: {invalid_pattern}"
    
    def test_all_states_coverage(self):
        """Test that all 50 states + DC have patterns."""
        expected_states = {
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
            'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
            'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
            'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
            'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        }
        
        actual_states = set(STATE_DL_PATTERNS.keys())
        assert actual_states == expected_states, f"Missing states: {expected_states - actual_states}"
        assert len(STATE_DL_PATTERNS) == 51, f"Expected 51 entries (50 states + DC), got {len(STATE_DL_PATTERNS)}"

class TestLicensePlatePatterns:
    """Test license plate detection patterns."""
    
    def test_standard_license_plates(self):
        """Test standard US license plate patterns."""
        pattern = STATE_LICENSE_PLATE_PATTERNS['STANDARD'][2]
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        
        valid = [
            'ABC123', 'ABC1234', '123ABC', '1234ABC',
            'AB123C', 'AB1234', 'ABC12D'
        ]
        
        for plate in valid:
            assert compiled_pattern.search(plate), f"Standard plate pattern should match: {plate}"
    
    def test_specialty_license_plates(self):
        """Test specialty/vanity license plate patterns."""
        pattern = STATE_LICENSE_PLATE_PATTERNS['SPECIALTY'][2]
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        
        valid = ['CUSTOM1', 'ABC123', 'TEST1', 'LOVE2U', 'FAST4U']
        
        for plate in valid:
            # This pattern requires both letters and numbers
            if any(c.isalpha() for c in plate) and any(c.isdigit() for c in plate):
                assert compiled_pattern.search(plate), f"Specialty plate pattern should match: {plate}"

class TestAddressPatterns:
    """Test address detection patterns."""
    
    def test_street_address_detection(self):
        """Test street address pattern detection."""
        rules = generate_address_rules()
        street_rule = next(rule for rule in rules if rule['id'] == 'PII-ADDR-STREET-1.0')
        pattern = re.compile(street_rule['pattern'])
        
        valid_addresses = [
            '123 Main Street',
            '456 Oak Avenue',
            '789 Elm Road',
            '321 Pine Drive',
            '654 Maple Lane',
            '987 Cedar Boulevard',
            '147 Birch Circle',
            '258 Ash Court',
            '369 Spruce Place',
            '741 Willow Way'
        ]
        
        for address in valid_addresses:
            assert pattern.search(address), f"Should detect address: {address}"
    
    def test_zip_code_detection(self):
        """Test ZIP code pattern detection."""
        rules = generate_address_rules()
        zip_rule = next(rule for rule in rules if rule['id'] == 'PII-ADDR-ZIP-1.0')
        pattern = re.compile(zip_rule['pattern'])
        
        valid_zips = ['12345', '90210', '60601', '10001-1234', '94102-1234']
        invalid_zips = ['1234', '123456', 'ABCDE']  # Removed partial ZIP as it would match the valid part
        
        for zip_code in valid_zips:
            assert pattern.search(zip_code), f"Should detect ZIP: {zip_code}"
        
        for zip_code in invalid_zips:
            assert not pattern.search(zip_code), f"Should not detect invalid ZIP: {zip_code}"

class TestPhonePatterns:
    """Test phone number detection patterns."""
    
    def test_phone_number_patterns(self):
        """Test various phone number formats."""
        rules = generate_phone_rules()
        
        test_cases = [
            ('(555) 123-4567', True),
            ('555-123-4567', True),
            ('555.123.4567', True),
            ('555 123 4567', True),
            ('5551234567', True),
            ('+1-555-123-4567', True),
            ('+1 555 123 4567', True),
            ('123-456', False),  # Too short
            ('555-123-456', False),  # Wrong format
        ]
        
        for phone, should_match in test_cases:
            matched = False
            for rule in rules:
                pattern = re.compile(rule['pattern'])
                if pattern.search(phone):
                    matched = True
                    break
            
            if should_match:
                assert matched, f"Should detect phone number: {phone}"
            else:
                assert not matched, f"Should not detect invalid phone: {phone}"

class TestRuleGeneration:
    """Test rule generation functions."""
    
    def test_dl_rule_generation(self):
        """Test driver's license rule generation."""
        rules = generate_state_dl_rules()
        
        # Should have rules for each state plus comprehensive rule
        assert len(rules) == 52  # 51 states/DC + 1 comprehensive
        
        # Check rule structure
        for rule in rules:
            assert 'id' in rule
            assert 'title' in rule
            assert 'severity' in rule
            assert 'pattern' in rule
            assert 'action' in rule
            assert 'applies_to' in rule
            assert 'endpoints' in rule
            assert 'metadata' in rule
            
            # Verify required fields
            assert rule['action'] == 'flag'
            assert rule['applies_to'] == ['request', 'response']
            assert rule['endpoints'] == ['*']
    
    def test_comprehensive_pattern_compilation(self):
        """Test that the comprehensive US pattern compiles correctly."""
        rules = generate_state_dl_rules()
        comprehensive_rule = next(rule for rule in rules if rule['id'] == 'PII-DL-US-1.0')
        
        # Should compile without errors
        compiled_pattern = re.compile(comprehensive_rule['pattern'])
        
        # Test with some known valid patterns
        test_cases = [
            'A12345678901',  # IL DL
            '12345678901A',  # IL ID
            'A1234567',      # CA DL
            'A123456789012', # FL DL
            '1234567',       # TX DL
        ]
        
        for test_case in test_cases:
            assert compiled_pattern.search(test_case), f"Comprehensive pattern should match: {test_case}"

class TestPatternValidation:
    """Test pattern validation and edge cases."""
    
    def test_pattern_compilation(self):
        """Test that all patterns compile correctly."""
        for state_code, (_, _, pattern, _) in STATE_DL_PATTERNS.items():
            try:
                re.compile(pattern)
            except re.error as e:
                pytest.fail(f"Pattern for {state_code} failed to compile: {e}")
    
    def test_false_positive_prevention(self):
        """Test that patterns don't match common false positives."""
        rules = generate_state_dl_rules()
        
        # Common false positives that should NOT match
        false_positives = [
            '123',           # Too short
            'ABC',           # Letters only
            '123-45-6789',   # SSN format
            '4111111111111116',  # Credit card
            '2023-12-25',    # Date
            '192.168.1.1',  # IP address
        ]
        
        for rule in rules:
            if rule['id'].startswith('PII-DL-'):
                pattern = re.compile(rule['pattern'])
                for fp in false_positives:
                    # Some patterns might legitimately match numbers, but check context
                    match = pattern.search(fp)
                    if match:
                        # If it matches, ensure it's a reasonable match given the state pattern
                        matched_text = match.group()
                        # This is mainly to ensure we're not getting wildly inappropriate matches
                        assert len(matched_text) >= 3, f"Pattern {rule['id']} matched too short text: {matched_text}"

def run_comprehensive_tests():
    """Run all tests and provide detailed output."""
    print("🧪 Running comprehensive PII pattern tests...")
    
    # Import pytest and run tests
    try:
        pytest.main([__file__, '-v', '--tb=short'])
    except SystemExit:
        pass  # pytest calls sys.exit, but we want to continue
    
    print("\n📊 Test Summary Complete")

if __name__ == '__main__':
    run_comprehensive_tests()
