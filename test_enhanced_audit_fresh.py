#!/usr/bin/env python3
"""
Test script to verify enhanced audit logging with fresh audit log
"""

import asyncio
import tempfile
import os
from pathlib import Path
from app.audit_logger import AuditLogger


async def test_enhanced_audit_fresh():
    """Test the enhanced audit logging system with a fresh file"""
    
    print("🔍 Testing Enhanced Audit Logging (Fresh Start)")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_log = Path(temp_dir) / "fresh_audit.jsonl"
        
        # Create a fresh audit logger
        logger = AuditLogger(test_log)
        
        print("1. Testing fresh audit chain creation...")
        
        # Log some test events
        logger.log_policy_decision(
            action="block",
            request_id="test-req-1", 
            direction="outbound",
            endpoint="/api/chat",
            rule_ids=["API-KEY-1.0", "GITHUB-TOKEN-1.0"],
            text_excerpt="sk-abc123def456..."
        )
        
        logger.log_policy_decision(
            action="flag",
            request_id="test-req-2",
            direction="inbound", 
            endpoint="/api/evaluate",
            rule_ids=["EMAIL-1.0"],
            text_excerpt="john.doe@company.com"
        )
        
        logger.log_policy_decision(
            action="allow",
            request_id="test-req-3",
            direction="inbound",
            endpoint="/api/test",
            rule_ids=[],
            text_excerpt="This is safe content"
        )
        
        print("✅ Successfully logged 3 fresh audit events")
        
        # Test chain verification
        print("\n2. Testing fresh chain integrity verification...")
        
        verification_result = logger.verify_chain()
        if verification_result["valid"]:
            print(f"✅ Fresh audit chain is valid with {verification_result['total_records']} records")
            print(f"   Verified {verification_result['verified_records']} of {verification_result['total_records']} records")
        else:
            print(f"❌ Fresh chain verification failed: {verification_result.get('error')}")
            return False
        
        # Test statistics
        print("\n3. Testing audit statistics...")
        
        stats = logger.get_chain_stats()
        print(f"✅ Total audit records: {stats['total_records']}")
        print(f"   - Blocked: {stats['actions'].get('block', 0)}")
        print(f"   - Flagged: {stats['actions'].get('flag', 0)}")
        print(f"   - Allowed: {stats['actions'].get('allow', 0)}")
        print(f"   Chain valid: {stats['chain_valid']}")
        if stats['date_range']:
            print(f"   Date range: {stats['date_range']['start'][:19]} to {stats['date_range']['end'][:19]}")
        
        # Test tamper detection
        print("\n4. Testing tamper detection...")
        
        # Read the file content
        with open(test_log, "r") as f:
            lines = f.readlines()
        
        # Tamper with the second record
        if len(lines) >= 2:
            # Modify the second line (corrupt a record)  
            lines[1] = lines[1].replace('"flag"', '"TAMPERED"')
            
            with open(test_log, "w") as f:
                f.writelines(lines)
            
            # Verify tamper detection
            tampered_result = logger.verify_chain()
            if not tampered_result["valid"]:
                print("✅ Tamper detection working - corrupted chain detected")
                print(f"   Error: {tampered_result.get('error')}")
            else:
                print("❌ Tamper detection failed - should have detected corruption")
                return False
        else:
            print("⚠️  Not enough records for tamper test")
        
        # Test admin/security events
        print("\n5. Testing admin and security event logging...")
        
        # Reset to clean state for more tests
        test_log.unlink()
        logger = AuditLogger(test_log)
        
        logger.log_admin_action(
            user_id="admin@company.com",
            action="access_granted", 
            resource="metrics"
        )
        
        logger.log_security_event(
            event_type="auth_failure",
            severity="high",
            description="Failed login attempt from suspicious IP",
            source_ip="192.168.1.100"
        )
        
        # Final verification
        print("\n6. Final chain verification...")
        final_verification = logger.verify_chain()
        if final_verification["valid"]:
            print(f"✅ Final audit chain integrity: VALID ({final_verification['total_records']} records)")
            
            # Show detailed chain info
            stats = logger.get_chain_stats()
            print(f"✅ Action breakdown:")
            for action, count in stats.get('actions', {}).items():
                print(f"   - {action}: {count}")
                
            return True
        else:
            print(f"❌ Final audit chain integrity: INVALID - {final_verification.get('error')}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_enhanced_audit_fresh())
    if success:
        print("\n🎉 Enhanced Audit Logging Test PASSED!")
        print("✅ Tamper-evident audit chains are working correctly")
    else:
        print("\n❌ Enhanced Audit Logging Test FAILED!")
    exit(0 if success else 1)