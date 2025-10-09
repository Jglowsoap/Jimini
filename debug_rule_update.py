#!/usr/bin/env python3
"""
Test script to debug the 422 error when updating rules
"""

import requests
import json


def test_rule_update():
    base_url = "http://localhost:9000"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "changeme"
    }
    
    # First, get the rule to see its current state
    print("Getting current rule...")
    response = requests.get(f"{base_url}/v1/rules/GITHUB-TOKEN-1.0", headers=headers)
    print(f"GET status: {response.status_code}")
    if response.status_code == 200:
        rule = response.json()
        print("Current rule:")
        print(json.dumps(rule, indent=2))
    else:
        print(f"GET failed: {response.text}")
        return
    
    # Try to update the rule
    print("\nUpdating rule...")
    update_data = {"action": "flag"}
    response = requests.put(
        f"{base_url}/v1/rules/GITHUB-TOKEN-1.0", 
        headers=headers,
        json=update_data
    )
    print(f"PUT status: {response.status_code}")
    print(f"PUT response: {response.text}")
    
    if response.status_code == 422:
        try:
            error = response.json()
            print("Validation error details:")
            print(json.dumps(error, indent=2))
        except:
            print("Could not parse error response as JSON")


if __name__ == "__main__":
    test_rule_update()