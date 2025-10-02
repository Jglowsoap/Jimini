"""
Comprehensive tests for tamper-evident audit chain validation
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any

from app.audit_logger import AuditLogger
from app.models import AuditRecord


class TestAuditChainValidation:
    """Test tamper-evident audit chain functionality"""
    
    @pytest.fixture
    def temp_audit_file(self):
        """Create temporary audit file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            audit_file = Path(f.name)
        yield audit_file
        # Cleanup
        if audit_file.exists():
            audit_file.unlink()
    
    @pytest.fixture  
    def audit_logger(self, temp_audit_file):
        """Create audit logger with temporary file"""
        return AuditLogger(temp_audit_file)
    
    def test_empty_chain_verification(self, audit_logger):
        """Test verification of empty audit chain"""
        result = audit_logger.verify_chain()
        
        assert result["valid"] is True
        assert result["total_records"] == 0
        assert result["verified_records"] == 0
        assert result["break_point"] is None
        assert result["error_message"] is None
    
    def test_single_record_chain(self, audit_logger):
        """Test single record audit chain"""
        # Add a single record
        record = audit_logger.log_policy_decision(
            action="block",
            request_id="test-123",
            direction="request",
            endpoint="/v1/evaluate",
            rule_ids=["TEST-1.0"],
            text_excerpt="test message"
        )
        
        # Verify the record was created correctly
        assert record.action == "block"
        assert record.request_id == "test-123" 
        assert record.previous_hash == audit_logger.genesis_hash
        assert len(record.text_hash) == 64  # SHA3-256 hex length
        
        # Verify chain integrity
        result = audit_logger.verify_chain()
        assert result["valid"] is True
        assert result["total_records"] == 1
        assert result["verified_records"] == 1
    
    def test_multi_record_chain(self, audit_logger):
        """Test multiple record audit chain"""
        # Add multiple records
        records = []
        for i in range(5):
            record = audit_logger.log_policy_decision(
                action=f"test_{i}",
                request_id=f"req-{i}",
                direction="request", 
                endpoint=f"/test/{i}",
                rule_ids=[f"RULE-{i}.0"],
                text_excerpt=f"test message {i}"
            )
            records.append(record)
        
        # Verify chain linking
        assert records[0].previous_hash == audit_logger.genesis_hash
        for i in range(1, len(records)):
            assert records[i].previous_hash == records[i-1].text_hash
        
        # Verify chain integrity
        result = audit_logger.verify_chain()
        assert result["valid"] is True
        assert result["total_records"] == 5
        assert result["verified_records"] == 5
        assert result["break_point"] is None
    
    def test_tamper_detection_modified_content(self, audit_logger):
        """Test detection of tampered record content"""
        # Add some records
        for i in range(3):
            audit_logger.log_policy_decision(
                action=f"test_{i}",
                request_id=f"req-{i}",
                direction="request",
                endpoint=f"/test/{i}",
                rule_ids=[f"RULE-{i}.0"],
                text_excerpt=f"test message {i}"
            )
        
        # Manually tamper with the audit file
        with audit_logger.audit_file.open("r") as f:
            lines = f.readlines()
        
        # Modify the second record
        if len(lines) >= 2:
            record_data = json.loads(lines[1])
            record_data["action"] = "tampered_action"  # Change the action
            lines[1] = json.dumps(record_data) + "\n"
            
            with audit_logger.audit_file.open("w") as f:
                f.writelines(lines)
        
        # Verify tamper detection
        result = audit_logger.verify_chain()
        assert result["valid"] is False
        assert result["break_point"] == 1  # Second record (0-indexed)
        assert "Hash verification failed" in result["error_message"]
    
    def test_tamper_detection_broken_chain(self, audit_logger):
        """Test detection of broken hash chain"""
        # Add some records
        for i in range(3):
            audit_logger.log_policy_decision(
                action=f"test_{i}",
                request_id=f"req-{i}",
                direction="request",
                endpoint=f"/test/{i}",
                rule_ids=[f"RULE-{i}.0"],
                text_excerpt=f"test message {i}"
            )
        
        # Manually break the hash chain
        with audit_logger.audit_file.open("r") as f:
            lines = f.readlines()
        
        # Modify the previous_hash of the second record
        if len(lines) >= 2:
            record_data = json.loads(lines[1])
            record_data["previous_hash"] = "0" * 64  # Invalid previous hash
            lines[1] = json.dumps(record_data) + "\n"
            
            with audit_logger.audit_file.open("w") as f:
                f.writelines(lines)
        
        # Verify chain break detection
        result = audit_logger.verify_chain()
        assert result["valid"] is False
        assert result["break_point"] == 1  # Second record (0-indexed)
        assert "Previous hash mismatch" in result["error_message"]
    
    def test_admin_action_logging(self, audit_logger):
        """Test logging of administrative actions"""
        record = audit_logger.log_admin_action(
            user_id="admin_user",
            action="update_config",
            resource="policy_rules",
            details={"changes": ["added RULE-NEW-1.0"]}
        )
        
        assert record.action == "admin_update_config"
        assert record.direction == "admin"
        assert record.endpoint == "/admin/policy_rules"
        assert "admin_user" in record.text_excerpt
        assert record.metadata["user_id"] == "admin_user"
        assert record.metadata["resource"] == "policy_rules"
        
        # Verify chain integrity
        result = audit_logger.verify_chain()
        assert result["valid"] is True
    
    def test_security_event_logging(self, audit_logger):
        """Test logging of security events"""
        record = audit_logger.log_security_event(
            event_type="authentication_failure",
            severity="high",
            description="Multiple failed login attempts",
            source_ip="192.168.1.100",
            user_id="suspicious_user"
        )
        
        assert record.action == "security_authentication_failure"
        assert record.direction == "security"
        assert record.endpoint == "/security/event"
        assert "Multiple failed login attempts" in record.text_excerpt
        assert record.metadata["severity"] == "high"
        assert record.metadata["source_ip"] == "192.168.1.100"
        
        # Verify chain integrity
        result = audit_logger.verify_chain()
        assert result["valid"] is True
    
    def test_record_filtering(self, audit_logger):
        """Test filtering of audit records"""
        # Add various types of records
        audit_logger.log_policy_decision("block", "req-1", "request", "/eval", ["RULE-1.0"])
        audit_logger.log_policy_decision("allow", "req-2", "request", "/eval", ["RULE-2.0"])
        audit_logger.log_admin_action("admin", "config_update", "rules")
        audit_logger.log_security_event("auth_fail", "medium", "Failed login")
        
        # Test action filtering
        blocked_records = audit_logger.get_records(action_filter="block")
        assert len(blocked_records) == 1
        assert blocked_records[0].action == "block"
        
        admin_records = audit_logger.get_records(action_filter="admin_")
        assert len(admin_records) == 1
        assert admin_records[0].action.startswith("admin_")
        
        security_records = audit_logger.get_records(action_filter="security_")
        assert len(security_records) == 1
        assert security_records[0].action.startswith("security_")
        
        # Test limit
        limited_records = audit_logger.get_records(limit=2)
        assert len(limited_records) == 2
    
    def test_chain_statistics(self, audit_logger):
        """Test audit chain statistics"""
        # Add some records
        audit_logger.log_policy_decision("block", "req-1", "request", "/eval", ["RULE-1.0"])
        audit_logger.log_policy_decision("allow", "req-2", "request", "/eval", ["RULE-2.0"])
        audit_logger.log_admin_action("admin", "config_update", "rules")
        
        stats = audit_logger.get_chain_stats()
        
        assert stats["total_records"] == 3
        assert stats["chain_valid"] is True
        assert "block" in stats["actions"]
        assert "allow" in stats["actions"]
        assert "admin_config_update" in stats["actions"]
        assert stats["actions"]["block"] == 1
        assert stats["actions"]["allow"] == 1
        assert stats["file_size_bytes"] > 0
        assert "start" in stats["date_range"]
        assert "end" in stats["date_range"]
    
    def test_export_functionality(self, audit_logger, temp_audit_file):
        """Test audit record export functionality"""
        # Add some test records
        audit_logger.log_policy_decision("block", "req-1", "request", "/eval", ["RULE-1.0"])
        audit_logger.log_admin_action("admin", "export", "audit_logs")
        
        # Test JSONL export
        export_file = temp_audit_file.with_suffix(".export.jsonl")
        result = audit_logger.export_records(export_file, format="jsonl")
        
        assert result["exported_records"] == 2
        assert result["format"] == "jsonl"
        assert result["chain_valid"] is True
        assert export_file.exists()
        
        # Verify exported content
        with export_file.open("r") as f:
            lines = f.readlines()
        assert len(lines) == 2
        
        # Test JSON export
        json_export = temp_audit_file.with_suffix(".export.json")
        result = audit_logger.export_records(json_export, format="json", include_verification=True)
        
        assert result["exported_records"] == 2
        assert json_export.exists()
        
        with json_export.open("r") as f:
            export_data = json.load(f)
        
        assert export_data["total_records"] == 2
        assert export_data["chain_verification"]["valid"] is True
        assert len(export_data["records"]) == 2
        
        # Cleanup
        export_file.unlink()
        json_export.unlink()
    
    def test_malformed_record_handling(self, audit_logger):
        """Test handling of malformed records in audit file"""
        # Add a valid record first
        audit_logger.log_policy_decision("allow", "req-1", "request", "/eval", ["RULE-1.0"])
        
        # Manually add a malformed record
        with audit_logger.audit_file.open("a") as f:
            f.write("invalid json line\n")
            f.write('{"incomplete": "json"\n')  # Missing closing brace
        
        # Add another valid record
        audit_logger.log_policy_decision("block", "req-2", "request", "/eval", ["RULE-2.0"])
        
        # Verification should handle malformed records gracefully
        records = list(audit_logger.iter_records())
        assert len(records) == 2  # Only valid records
        
        # Chain verification should work with valid records
        result = audit_logger.verify_chain()
        assert result["valid"] is True
        assert result["total_records"] == 2


def test_audit_integration():
    """Integration test for audit system"""
    # Test the global audit logger functions
    from app.audit_logger import log_policy_decision, verify_audit_chain, get_audit_stats
    
    # Log some decisions
    record1 = log_policy_decision(
        action="block",
        request_id="integration-test-1",
        direction="request",
        endpoint="/v1/evaluate",
        rule_ids=["INTEGRATION-1.0"],
        text_excerpt="integration test message",
        metadata={"test": True}
    )
    
    record2 = log_policy_decision(
        action="allow",
        request_id="integration-test-2", 
        direction="response",
        endpoint="/v1/evaluate",
        rule_ids=["INTEGRATION-2.0"],
        text_excerpt="second test message"
    )
    
    # Verify records are linked correctly
    assert record1.previous_hash == "0" * 64  # First record links to genesis
    assert record2.previous_hash == record1.text_hash  # Second links to first
    
    # Verify chain integrity
    verification = verify_audit_chain()
    assert verification["valid"] is True
    assert verification["total_records"] >= 2  # At least our test records
    
    # Get statistics
    stats = get_audit_stats()
    assert stats["chain_valid"] is True
    assert stats["total_records"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])