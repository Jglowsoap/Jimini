"""
Enhanced Tamper-Evident Audit Logger for Jimini
Implements cryptographically secure audit chains with integrity verification
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator
import uuid

from app.models import AuditRecord
from app.util import now_iso


class AuditLogger:
    """
    Tamper-evident audit logger with SHA3-256 hash chains.
    Each record is cryptographically linked to prevent tampering.
    """
    
    def __init__(self, audit_file: Optional[Path] = None):
        self.audit_file = audit_file or Path(os.getenv("AUDIT_LOG_PATH", "logs/audit.jsonl"))
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        self.genesis_hash = "0" * 64  # Genesis block hash
        
    def _canonical_json(self, obj: Dict[str, Any]) -> str:
        """Create deterministic JSON for hashing"""
        return json.dumps(obj, sort_keys=True, separators=(",", ":"))
    
    def _sha3_256_hex(self, data: str) -> str:
        """Generate SHA3-256 hex digest"""
        return hashlib.sha3_256(data.encode("utf-8")).hexdigest()
    
    def _get_last_hash(self) -> str:
        """Get the hash of the last record in the chain"""
        if not self.audit_file.exists():
            return self.genesis_hash
            
        last_hash = self.genesis_hash
        try:
            with self.audit_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record_data = json.loads(line)
                            if "text_hash" in record_data:
                                last_hash = record_data["text_hash"]
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
            
        return last_hash
    
    def log_policy_decision(self, 
                          action: str,
                          request_id: str,
                          direction: str,
                          endpoint: str,
                          rule_ids: List[str],
                          text_excerpt: str = "",
                          metadata: Optional[Dict[str, Any]] = None) -> AuditRecord:
        """
        Log a policy decision with tamper-evident chaining
        
        Args:
            action: Policy decision (block, flag, allow)
            request_id: Unique request identifier
            direction: request or response
            endpoint: API endpoint that was evaluated
            rule_ids: List of rule IDs that matched
            text_excerpt: Redacted text sample for audit
            metadata: Additional context data
            
        Returns:
            The created AuditRecord
        """
        # Get previous hash for chaining
        previous_hash = self._get_last_hash()
        
        # Create the audit record
        timestamp = now_iso()
        
        # Build the payload for hashing (exclude hash fields)
        payload = {
            "timestamp": timestamp,
            "request_id": request_id,
            "action": action,
            "direction": direction,
            "endpoint": endpoint,
            "rule_ids": rule_ids,
            "text_excerpt": text_excerpt
        }
        
        # Calculate the chain hash
        payload_json = self._canonical_json(payload)
        text_hash = self._sha3_256_hex(previous_hash + payload_json)
        
        # Create the audit record
        audit_record = AuditRecord(
            timestamp=timestamp,
            request_id=request_id,
            action=action,
            direction=direction,
            endpoint=endpoint,
            rule_ids=rule_ids,
            text_excerpt=text_excerpt,
            text_hash=text_hash,
            previous_hash=previous_hash,
            metadata=metadata or {}
        )
        
        # Write to file
        with self.audit_file.open("a", encoding="utf-8") as f:
            f.write(audit_record.model_dump_json() + "\n")
        
        return audit_record
    
    def log_admin_action(self,
                        user_id: str,
                        action: str,
                        resource: str,
                        details: Optional[Dict[str, Any]] = None) -> AuditRecord:
        """
        Log administrative actions (user management, config changes, etc.)
        """
        return self.log_policy_decision(
            action=f"admin_{action}",
            request_id=str(uuid.uuid4()),
            direction="admin",
            endpoint=f"/admin/{resource}",
            rule_ids=[],
            text_excerpt=f"User {user_id} performed {action} on {resource}",
            metadata={
                "user_id": user_id,
                "resource": resource,
                "details": details or {}
            }
        )
    
    def log_security_event(self,
                          event_type: str,
                          severity: str,
                          description: str,
                          source_ip: Optional[str] = None,
                          user_id: Optional[str] = None) -> AuditRecord:
        """
        Log security events (authentication failures, suspicious activity, etc.)
        """
        return self.log_policy_decision(
            action=f"security_{event_type}",
            request_id=str(uuid.uuid4()),
            direction="security",
            endpoint="/security/event",
            rule_ids=[],
            text_excerpt=description,
            metadata={
                "event_type": event_type,
                "severity": severity,
                "source_ip": source_ip,
                "user_id": user_id
            }
        )
    
    def verify_chain(self) -> Dict[str, Any]:
        """
        Verify the integrity of the entire audit chain
        
        Returns:
            Dictionary with verification results:
            {
                "valid": bool,
                "total_records": int,
                "verified_records": int,
                "break_point": Optional[int],  # Index where chain breaks
                "error_message": Optional[str]
            }
        """
        if not self.audit_file.exists():
            return {
                "valid": True,
                "total_records": 0,
                "verified_records": 0,
                "break_point": None,
                "error_message": None
            }
        
        records = list(self.iter_records())
        if not records:
            return {
                "valid": True,
                "total_records": 0,
                "verified_records": 0,
                "break_point": None,
                "error_message": None
            }
        
        previous_hash = self.genesis_hash
        verified_count = 0
        
        for i, record in enumerate(records):
            try:
                # Verify previous hash link
                if record.previous_hash != previous_hash:
                    return {
                        "valid": False,
                        "total_records": len(records),
                        "verified_records": verified_count,
                        "break_point": i,
                        "error_message": f"Previous hash mismatch at record {i}"
                    }
                
                # Rebuild payload and verify hash
                payload = {
                    "timestamp": record.timestamp,
                    "request_id": record.request_id,
                    "action": record.action,
                    "direction": record.direction,
                    "endpoint": record.endpoint,
                    "rule_ids": record.rule_ids,
                    "text_excerpt": record.text_excerpt
                }
                
                expected_hash = self._sha3_256_hex(previous_hash + self._canonical_json(payload))
                
                if record.text_hash != expected_hash:
                    return {
                        "valid": False,
                        "total_records": len(records),
                        "verified_records": verified_count,
                        "break_point": i,
                        "error_message": f"Hash verification failed at record {i}"
                    }
                
                previous_hash = record.text_hash
                verified_count += 1
                
            except Exception as e:
                return {
                    "valid": False,
                    "total_records": len(records),
                    "verified_records": verified_count,
                    "break_point": i,
                    "error_message": f"Error processing record {i}: {str(e)}"
                }
        
        return {
            "valid": True,
            "total_records": len(records),
            "verified_records": verified_count,
            "break_point": None,
            "error_message": None
        }
    
    def iter_records(self) -> Iterator[AuditRecord]:
        """Iterate over all audit records in the file"""
        if not self.audit_file.exists():
            return
            
        with self.audit_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    yield AuditRecord(**data)
                except Exception as e:
                    # Log malformed records but continue processing
                    print(f"Warning: Malformed audit record at line {line_num}: {e}")
                    continue
    
    def get_records(self, 
                   limit: Optional[int] = None,
                   action_filter: Optional[str] = None,
                   date_filter: Optional[str] = None) -> List[AuditRecord]:
        """
        Retrieve audit records with optional filtering
        
        Args:
            limit: Maximum number of records to return
            action_filter: Filter by action type (e.g., "block", "admin_", "security_")
            date_filter: Filter by date prefix (e.g., "2024-01-01")
            
        Returns:
            List of matching audit records
        """
        records = []
        count = 0
        
        for record in self.iter_records():
            # Apply filters
            if action_filter and not record.action.startswith(action_filter):
                continue
                
            if date_filter and not record.timestamp.startswith(date_filter):
                continue
            
            records.append(record)
            count += 1
            
            if limit and count >= limit:
                break
        
        return records
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Get statistics about the audit chain"""
        records = list(self.iter_records())
        
        if not records:
            return {
                "total_records": 0,
                "date_range": None,
                "actions": {},
                "file_size_bytes": 0,
                "chain_valid": True
            }
        
        # Count actions
        action_counts = {}
        for record in records:
            action_counts[record.action] = action_counts.get(record.action, 0) + 1
        
        # Get file size
        file_size = self.audit_file.stat().st_size if self.audit_file.exists() else 0
        
        # Check chain validity
        verification = self.verify_chain()
        
        return {
            "total_records": len(records),
            "date_range": {
                "start": records[0].timestamp,
                "end": records[-1].timestamp
            },
            "actions": action_counts,
            "file_size_bytes": file_size,
            "chain_valid": verification["valid"],
            "verification_details": verification
        }
    
    def export_records(self, 
                      output_file: Path,
                      format: str = "jsonl",
                      include_verification: bool = True) -> Dict[str, Any]:
        """
        Export audit records to a file with optional integrity verification
        
        Args:
            output_file: Path to write exported records
            format: Export format ("jsonl", "json", "csv")
            include_verification: Include chain verification in export
            
        Returns:
            Export summary with statistics
        """
        records = list(self.iter_records())
        verification = self.verify_chain() if include_verification else None
        
        export_data = {
            "export_timestamp": now_iso(),
            "source_file": str(self.audit_file),
            "total_records": len(records),
            "chain_verification": verification,
            "records": [record.model_dump() for record in records]
        }
        
        if format == "json":
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
        elif format == "jsonl":
            with output_file.open("w", encoding="utf-8") as f:
                for record in records:
                    f.write(record.model_dump_json() + "\n")
        elif format == "csv":
            import csv
            with output_file.open("w", newline="", encoding="utf-8") as f:
                if records:
                    writer = csv.DictWriter(f, fieldnames=records[0].model_dump().keys())
                    writer.writeheader()
                    for record in records:
                        writer.writerow(record.model_dump())
        
        return {
            "exported_records": len(records),
            "output_file": str(output_file),
            "format": format,
            "chain_valid": verification["valid"] if verification else None
        }


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None

def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger

def log_policy_decision(action: str, request_id: str, direction: str, 
                       endpoint: str, rule_ids: List[str], text_excerpt: str = "",
                       metadata: Optional[Dict[str, Any]] = None) -> AuditRecord:
    """Convenience function for logging policy decisions"""
    return get_audit_logger().log_policy_decision(
        action, request_id, direction, endpoint, rule_ids, text_excerpt, metadata
    )

def verify_audit_chain() -> Dict[str, Any]:
    """Convenience function for verifying audit chain integrity"""
    return get_audit_logger().verify_chain()

def get_audit_stats() -> Dict[str, Any]:
    """Convenience function for getting audit chain statistics"""
    return get_audit_logger().get_chain_stats()