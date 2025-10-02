#!/usr/bin/env python3
"""
Test script to verify enhanced audit logging integration with main API
"""

import asyncio
import tempfile
import os
from pathlib import Path
from app.audit_logger import log_policy_decision, verify_audit_chain, get_audit_stats, AuditLogger


async def test_enhanced_audit_integration():
    """Test the enhanced audit logging system integration"""
    
    print("🔍 Testing Enhanced Audit Logging Integration")
    print("=" * 60)
    
    # Test 1: Basic audit event logging
    print("\n1. Testing basic audit event logging...")
    
    # Log some test events using policy decision function
    log_policy_decision(
        action="block",
        request_id="test-req-1",
        direction="outbound",
        endpoint="/api/chat",
        rule_ids=["API-KEY-1.0", "GITHUB-TOKEN-1.0"],
        text_excerpt="sk-abc123def456..."
    )
    
    log_policy_decision(
        action="flag",
        request_id="test-req-2", 
        direction="inbound",
        endpoint="/api/evaluate",
        rule_ids=["EMAIL-1.0"],
        text_excerpt="john.doe@company.com"
    )
    
    log_policy_decision(
        action="allow",
        request_id="test-req-3",
        direction="inbound",
        endpoint="/api/test",
        rule_ids=[],
        text_excerpt="This is safe content"
    )
    
    print("✅ Successfully logged 3 audit events")
    
    # Test 2: Chain verification
    print("\n2. Testing chain integrity verification...")
    
    verification_result = verify_audit_chain()
    if verification_result["is_valid"]:
        print(f"✅ Audit chain is valid with {verification_result['total_records']} records")
        print(f"   Chain hash: {verification_result['chain_hash'][:16]}...")
    else:
        print(f"❌ Chain verification failed: {verification_result.get('error')}")
    
    # Test 3: Audit statistics
    print("\n3. Testing audit statistics...")
    
    stats = get_audit_stats()
    print(f"✅ Total audit records: {stats['total_records']}")
    print(f"   - Blocked: {stats['action_counts'].get('block', 0)}")
    print(f"   - Flagged: {stats['action_counts'].get('flag', 0)}")  
    print(f"   - Allowed: {stats['action_counts'].get('allow', 0)}")
    print(f"   Most active rule: {stats['top_rules'][0] if stats['top_rules'] else 'None'}")
    
    # Test 4: Tamper detection with AuditLogger class
    print("\n4. Testing tamper detection capabilities...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_log = os.path.join(temp_dir, "test_audit.jsonl")
        logger = AuditLogger(Path(test_log))
        
        # Add some records
        logger.log_policy_decision("block", "test-1", "inbound", "/test", ["TEST-1.0"], "test content 1")
        logger.log_policy_decision("flag", "test-2", "outbound", "/test", ["TEST-2.0"], "test content 2") 
        
        # Verify initial integrity
        result = logger.verify_chain()
        if result["is_valid"]:
            print("✅ Test audit chain initially valid")
            
            # Tamper with the file
            with open(test_log, "r") as f:
                lines = f.readlines()
            
            if len(lines) >= 2:
                # Modify the second line (corrupt a record)
                lines[1] = lines[1].replace("flag", "TAMPERED")
                
                with open(test_log, "w") as f:
                    f.writelines(lines)
                
                # Verify tamper detection
                tampered_result = logger.verify_chain()
                if not tampered_result["is_valid"]:
                    print("✅ Tamper detection working - corrupted chain detected")
                else:
                    print("❌ Tamper detection failed - should have detected corruption")
            else:
                print("⚠️  Not enough records for tamper test")
        else:
            print(f"❌ Test chain verification failed: {result.get('error')}")
    
    # Test 5: Admin/Security event logging
    print("\n5. Testing additional policy decision logging...")
    
    log_policy_decision(
        action="block",
        request_id="admin-req-1",
        direction="inbound",
        endpoint="/admin/metrics",
        rule_ids=["ADMIN-ACCESS-1.0"],
        text_excerpt="Unauthorized admin access attempt"
    )
    
    log_policy_decision(
        action="flag",
        request_id="security-req-1",
        direction="inbound",
        endpoint="/auth/login",
        rule_ids=["SECURITY-BREACH-1.0"],
        text_excerpt="Suspicious login pattern detected"
    )
    
    # Get updated stats
    final_stats = get_audit_stats()
    print(f"✅ Final audit record count: {final_stats['total_records']}")
    print(f"   Event types: {list(final_stats.get('event_types', {}).keys())}")
    
    print("\n" + "=" * 60)
    print("🎉 Enhanced Audit Integration Test Complete!")
    
    # Verification summary
    final_verification = verify_audit_chain()
    if final_verification["is_valid"]:
        print(f"✅ Final audit chain integrity: VALID ({final_verification['total_records']} records)")
        return True
    else:
        print(f"❌ Final audit chain integrity: INVALID - {final_verification.get('error')}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_enhanced_audit_integration())
    exit(0 if success else 1)