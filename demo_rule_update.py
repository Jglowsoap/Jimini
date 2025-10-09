#!/usr/bin/env python3
"""
Demo: Change Rule Action from BLOCK to FLAG

This script demonstrates how to use the Jimini API to update a rule's action
from 'block' to 'flag' (or vice versa) on the fly.

Usage:
    python demo_rule_update.py --rule-id GITHUB-TOKEN-1.0 --new-action flag
    python demo_rule_update.py --rule-id GITHUB-TOKEN-1.0 --new-action block
"""

import requests
import json
import argparse
from typing import Optional


class JiminiClient:
    """Simple client for Jimini API operations"""
    
    def __init__(self, base_url: str = "http://localhost:9000", api_key: str = "changeme"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
    
    def get_rule(self, rule_id: str) -> Optional[dict]:
        """Get a specific rule by ID"""
        try:
            response = requests.get(
                f"{self.base_url}/v1/rules/{rule_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting rule {rule_id}: {e}")
            return None
    
    def update_rule_action(self, rule_id: str, new_action: str) -> bool:
        """Update a rule's action"""
        try:
            # Get current rule to show the change
            current_rule = self.get_rule(rule_id)
            if not current_rule:
                print(f"❌ Rule {rule_id} not found")
                return False
            
            print(f"📋 Current rule '{rule_id}':")
            print(f"   Title: {current_rule.get('title', 'N/A')}")
            print(f"   Current Action: {current_rule.get('action', 'N/A')}")
            print(f"   Pattern: {current_rule.get('pattern', 'N/A')}")
            
            if current_rule.get('action') == new_action:
                print(f"✅ Rule is already set to '{new_action}' - no change needed")
                return True
            
            # Update the rule
            update_data = {"action": new_action}
            response = requests.put(
                f"{self.base_url}/v1/rules/{rule_id}",
                headers=self.headers,
                json=update_data
            )
            response.raise_for_status()
            
            updated_rule = response.json()
            print(f"\n🔄 Successfully updated rule '{rule_id}':")
            print(f"   Old Action: {current_rule.get('action', 'N/A')}")
            print(f"   New Action: {updated_rule.get('action', 'N/A')}")
            
            return True
            
        except requests.RequestException as e:
            print(f"❌ Error updating rule {rule_id}: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Status code: {e.response.status_code}")
                try:
                    error_detail = e.response.json()
                    print(f"   Details: {error_detail}")
                except:
                    print(f"   Response text: {e.response.text}")
            return False
    
    def list_rules(self, limit: int = 5) -> list:
        """List first few rules for reference"""
        try:
            response = requests.get(
                f"{self.base_url}/v1/rules?page_size={limit}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get('rules', [])
        except requests.RequestException as e:
            print(f"Error listing rules: {e}")
            return []
    
    def test_rule_effect(self, test_text: str) -> dict:
        """Test how the current rules evaluate some text"""
        try:
            response = requests.post(
                f"{self.base_url}/v1/evaluate",
                headers=self.headers,
                json={
                    "text": test_text,
                    "direction": "input",
                    "endpoint": "/test"
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error testing evaluation: {e}")
            return {}


def main():
    parser = argparse.ArgumentParser(description='Demo: Change Jimini rule action')
    parser.add_argument('--rule-id', required=True, help='Rule ID to update (e.g., GITHUB-TOKEN-1.0)')
    parser.add_argument('--new-action', required=True, choices=['block', 'flag', 'allow'], help='New action for the rule')
    parser.add_argument('--base-url', default='http://localhost:9000', help='Jimini API base URL')
    parser.add_argument('--api-key', default='changeme', help='API key for authentication')
    parser.add_argument('--test', action='store_true', help='Run a test evaluation after updating')
    
    args = parser.parse_args()
    
    print("🚀 Jimini Rule Update Demo")
    print("=" * 50)
    
    client = JiminiClient(args.base_url, args.api_key)
    
    # Update the rule
    success = client.update_rule_action(args.rule_id, args.new_action)
    
    if success and args.test:
        print(f"\n🧪 Testing rule effect...")
        
        # Create test cases based on the rule
        test_cases = {
            'GITHUB-TOKEN-1.0': 'ghp_1234567890123456789012345678901234567890',
            'OPENAI-KEY-1.0': 'sk-proj-abcd1234567890',
            'EMAIL-1.0': 'test@example.com',
            'API-1.0': 'very-long-api-key-12345678901234567890'
        }
        
        test_text = test_cases.get(args.rule_id, "test input")
        result = client.test_rule_effect(test_text)
        
        if result:
            print(f"   Test input: '{test_text}'")
            print(f"   Decision: {result.get('decision', 'N/A')}")
            print(f"   Matched rules: {result.get('rule_ids', [])}")
        
    print(f"\n✨ Demo complete!")


if __name__ == "__main__":
    main()