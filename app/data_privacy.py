"""
Data Management & Privacy Module for GDPR/CCPA Compliance

Provides:
- GDPR/CCPA right-to-access endpoints
- Right-to-be-forgotten (deletion/redaction)
- Configurable retention policies
- Privacy-by-default redaction levels
- Automated data lifecycle management
"""

import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
from enum import Enum
import structlog
from pydantic import BaseModel, Field
from fastapi import HTTPException, status

from app.models import AuditRecord
from app.config import get_config

logger = structlog.get_logger()


class RedactionLevel(str, Enum):
    """Privacy redaction levels."""
    NONE = "none"
    PARTIAL = "partial" 
    FULL = "full"


class RetentionPolicy(BaseModel):
    """Data retention policy configuration."""
    audit_retention_days: int = Field(default=90, ge=1, le=2555)  # 7 years max
    telemetry_retention_days: int = Field(default=30, ge=1, le=365)
    deadletter_retention_days: int = Field(default=7, ge=1, le=30)
    auto_cleanup_enabled: bool = Field(default=True)
    redaction_level: RedactionLevel = Field(default=RedactionLevel.PARTIAL)


class DataExportRequest(BaseModel):
    """Request for data export."""
    user_id: str = Field(..., min_length=1, max_length=256)
    include_audit: bool = Field(default=True)
    include_telemetry: bool = Field(default=True)
    date_from: Optional[datetime] = Field(default=None)
    date_to: Optional[datetime] = Field(default=None)
    format: str = Field(default="json", pattern="^(json|csv)$")


class DataDeletionRequest(BaseModel):
    """Request for data deletion/redaction."""
    user_id: str = Field(..., min_length=1, max_length=256)
    deletion_type: str = Field(default="redact", pattern="^(delete|redact)$")
    reason: str = Field(..., min_length=1, max_length=512)
    confirm: bool = Field(default=False)


class DataExportResponse(BaseModel):
    """Response for data export."""
    user_id: str
    export_date: datetime
    total_records: int
    audit_records: List[Dict[str, Any]]
    telemetry_records: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class DataManager:
    """Manages data lifecycle, privacy, and compliance operations."""
    
    def __init__(self):
        self.config = get_config()
        self.retention_policy = self._load_retention_policy()
        self.audit_log_path = Path(self.config.audit_log_path)
        self.telemetry_log_path = Path("logs/jimini_events.jsonl")
        
    def _load_retention_policy(self) -> RetentionPolicy:
        """Load retention policy from configuration."""
        try:
            policy_config = self.config.privacy_settings
            return RetentionPolicy(**policy_config)
        except Exception as e:
            logger.warning(f"Failed to load retention policy, using defaults: {e}")
            return RetentionPolicy()
    
    async def export_user_data(self, request: DataExportRequest) -> DataExportResponse:
        """Export all user data for GDPR/CCPA compliance."""
        logger.info(f"Starting data export for user: {request.user_id}")
        
        audit_records = []
        telemetry_records = []
        
        try:
            # Export audit records
            if request.include_audit:
                audit_records = await self._export_audit_records(
                    request.user_id, 
                    request.date_from, 
                    request.date_to
                )
            
            # Export telemetry records
            if request.include_telemetry:
                telemetry_records = await self._export_telemetry_records(
                    request.user_id,
                    request.date_from,
                    request.date_to
                )
            
            # Create export response
            export_response = DataExportResponse(
                user_id=request.user_id,
                export_date=datetime.utcnow(),
                total_records=len(audit_records) + len(telemetry_records),
                audit_records=audit_records,
                telemetry_records=telemetry_records,
                metadata={
                    "export_format": request.format,
                    "date_range": {
                        "from": request.date_from.isoformat() if request.date_from else None,
                        "to": request.date_to.isoformat() if request.date_to else None
                    },
                    "redaction_level": self.retention_policy.redaction_level.value,
                    "export_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Data export completed for user {request.user_id}: {export_response.total_records} records")
            return export_response
            
        except Exception as e:
            logger.error(f"Data export failed for user {request.user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data export failed: {str(e)}"
            )
    
    async def delete_user_data(self, request: DataDeletionRequest) -> Dict[str, Any]:
        """Delete or redact user data for right-to-be-forgotten."""
        if not request.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deletion must be confirmed with confirm=true"
            )
        
        logger.info(f"Starting data deletion for user: {request.user_id}, type: {request.deletion_type}")
        
        try:
            results = {
                "user_id": request.user_id,
                "deletion_type": request.deletion_type,
                "reason": request.reason,
                "timestamp": datetime.utcnow().isoformat(),
                "records_processed": 0,
                "files_modified": []
            }
            
            # Process audit logs
            audit_results = await self._process_audit_deletion(request.user_id, request.deletion_type)
            results["audit_records_processed"] = audit_results["records_processed"]
            results["files_modified"].extend(audit_results["files_modified"])
            
            # Process telemetry logs
            telemetry_results = await self._process_telemetry_deletion(request.user_id, request.deletion_type)
            results["telemetry_records_processed"] = telemetry_results["records_processed"]
            results["files_modified"].extend(telemetry_results["files_modified"])
            
            results["records_processed"] = (
                results["audit_records_processed"] + 
                results["telemetry_records_processed"]
            )
            
            # Log deletion for compliance audit
            await self._log_deletion_action(results)
            
            logger.info(f"Data deletion completed for user {request.user_id}: {results['records_processed']} records")
            return results
            
        except Exception as e:
            logger.error(f"Data deletion failed for user {request.user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data deletion failed: {str(e)}"
            )
    
    async def _export_audit_records(self, user_id: str, date_from: Optional[datetime], date_to: Optional[datetime]) -> List[Dict[str, Any]]:
        """Export audit records for a specific user."""
        records = []
        
        try:
            # Read audit log files
            audit_files = self._get_audit_log_files()
            
            for audit_file in audit_files:
                if not audit_file.exists():
                    continue
                    
                with open(audit_file, 'r') as f:
                    for line in f:
                        try:
                            record = json.loads(line.strip())
                            
                            # Check if record belongs to user
                            if self._record_belongs_to_user(record, user_id):
                                # Check date range
                                if self._is_in_date_range(record, date_from, date_to):
                                    # Apply redaction
                                    redacted_record = self._apply_redaction(record)
                                    records.append(redacted_record)
                                    
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Failed to export audit records: {e}")
            
        return records
    
    async def _export_telemetry_records(self, user_id: str, date_from: Optional[datetime], date_to: Optional[datetime]) -> List[Dict[str, Any]]:
        """Export telemetry records for a specific user.""" 
        records = []
        
        try:
            if self.telemetry_log_path.exists():
                with open(self.telemetry_log_path, 'r') as f:
                    for line in f:
                        try:
                            record = json.loads(line.strip())
                            
                            # Check if record belongs to user
                            if self._record_belongs_to_user(record, user_id):
                                # Check date range
                                if self._is_in_date_range(record, date_from, date_to):
                                    # Apply redaction
                                    redacted_record = self._apply_redaction(record)
                                    records.append(redacted_record)
                                    
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Failed to export telemetry records: {e}")
            
        return records
    
    def _record_belongs_to_user(self, record: Dict[str, Any], user_id: str) -> bool:
        """Check if a record belongs to the specified user."""
        # Check various fields that might contain user identification
        user_fields = ["user_id", "username", "email", "session_id", "api_key_id"]
        
        for field in user_fields:
            if field in record and str(record[field]) == user_id:
                return True
                
        # Check in nested objects
        if "metadata" in record and isinstance(record["metadata"], dict):
            for field in user_fields:
                if field in record["metadata"] and str(record["metadata"][field]) == user_id:
                    return True
                    
        return False
    
    def _is_in_date_range(self, record: Dict[str, Any], date_from: Optional[datetime], date_to: Optional[datetime]) -> bool:
        """Check if record is within specified date range."""
        if not date_from and not date_to:
            return True
            
        record_timestamp = self._extract_timestamp(record)
        if not record_timestamp:
            return True  # Include records without timestamps to be safe
            
        if date_from and record_timestamp < date_from:
            return False
            
        if date_to and record_timestamp > date_to:
            return False
            
        return True
    
    def _extract_timestamp(self, record: Dict[str, Any]) -> Optional[datetime]:
        """Extract timestamp from record."""
        timestamp_fields = ["timestamp", "created_at", "event_time", "@timestamp"]
        
        for field in timestamp_fields:
            if field in record:
                try:
                    if isinstance(record[field], str):
                        return datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                    elif isinstance(record[field], (int, float)):
                        return datetime.fromtimestamp(record[field])
                except (ValueError, TypeError):
                    continue
                    
        return None
    
    def _apply_redaction(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Apply privacy redaction based on configured level."""
        if self.retention_policy.redaction_level == RedactionLevel.NONE:
            return record
            
        redacted = record.copy()
        
        if self.retention_policy.redaction_level == RedactionLevel.PARTIAL:
            # Redact sensitive fields but keep structure
            sensitive_fields = ["text", "content", "message", "data", "payload"]
            for field in sensitive_fields:
                if field in redacted:
                    redacted[field] = "[REDACTED]"
        
        elif self.retention_policy.redaction_level == RedactionLevel.FULL:
            # Keep only essential metadata
            essential_fields = ["timestamp", "event_type", "decision", "rule_ids", "user_id"]
            redacted = {k: v for k, v in redacted.items() if k in essential_fields}
            
        return redacted
    
    async def _process_audit_deletion(self, user_id: str, deletion_type: str) -> Dict[str, Any]:
        """Process audit log deletion/redaction."""
        results = {"records_processed": 0, "files_modified": []}
        
        audit_files = self._get_audit_log_files()
        
        for audit_file in audit_files:
            if not audit_file.exists():
                continue
                
            modified = await self._process_log_file_deletion(audit_file, user_id, deletion_type)
            if modified:
                results["files_modified"].append(str(audit_file))
                
        return results
    
    async def _process_telemetry_deletion(self, user_id: str, deletion_type: str) -> Dict[str, Any]:
        """Process telemetry log deletion/redaction."""
        results = {"records_processed": 0, "files_modified": []}
        
        if self.telemetry_log_path.exists():
            modified = await self._process_log_file_deletion(self.telemetry_log_path, user_id, deletion_type)
            if modified:
                results["files_modified"].append(str(self.telemetry_log_path))
                
        return results
    
    async def _process_log_file_deletion(self, log_file: Path, user_id: str, deletion_type: str) -> bool:
        """Process deletion/redaction in a single log file."""
        temp_file = log_file.with_suffix(".tmp")
        modified = False
        
        try:
            with open(log_file, 'r') as infile, open(temp_file, 'w') as outfile:
                for line in infile:
                    try:
                        record = json.loads(line.strip())
                        
                        if self._record_belongs_to_user(record, user_id):
                            modified = True
                            if deletion_type == "redact":
                                # Redact the record but keep it
                                redacted_record = self._apply_redaction(record)
                                redacted_record["_redacted"] = True
                                redacted_record["_redaction_timestamp"] = datetime.utcnow().isoformat()
                                outfile.write(json.dumps(redacted_record) + "\n")
                            # If deletion_type == "delete", skip writing the record
                        else:
                            # Keep records not belonging to the user
                            outfile.write(line)
                            
                    except json.JSONDecodeError:
                        # Keep malformed lines as-is
                        outfile.write(line)
            
            if modified:
                # Replace original with modified file
                temp_file.replace(log_file)
            else:
                # Remove temp file if no changes
                temp_file.unlink()
                
        except Exception as e:
            logger.error(f"Failed to process log file {log_file}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise
            
        return modified
    
    def _get_audit_log_files(self) -> List[Path]:
        """Get list of audit log files to process."""
        files = []
        
        # Current audit log
        if self.audit_log_path.exists():
            files.append(self.audit_log_path)
            
        # Rotated audit logs
        log_dir = self.audit_log_path.parent
        if log_dir.exists():
            for file in log_dir.glob("audit-*.jsonl"):
                files.append(file)
                
        return files
    
    async def _log_deletion_action(self, deletion_results: Dict[str, Any]):
        """Log the deletion action for compliance audit trail."""
        deletion_record = {
            "event_type": "data_deletion",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": deletion_results["user_id"],
            "deletion_type": deletion_results["deletion_type"],
            "reason": deletion_results["reason"],
            "records_processed": deletion_results["records_processed"],
            "files_modified": deletion_results["files_modified"]
        }
        
        # Write to a separate compliance log
        compliance_log = Path("logs/compliance_actions.jsonl")
        compliance_log.parent.mkdir(exist_ok=True)
        
        with open(compliance_log, 'a') as f:
            f.write(json.dumps(deletion_record) + "\n")
    
    async def cleanup_expired_data(self):
        """Automated cleanup of expired data based on retention policy."""
        if not self.retention_policy.auto_cleanup_enabled:
            logger.info("Auto-cleanup disabled, skipping")
            return
            
        logger.info("Starting automated data cleanup")
        
        cleanup_results = {
            "audit_files_cleaned": 0,
            "telemetry_records_cleaned": 0,
            "deadletter_records_cleaned": 0
        }
        
        try:
            # Cleanup audit logs
            await self._cleanup_audit_logs(cleanup_results)
            
            # Cleanup telemetry logs  
            await self._cleanup_telemetry_logs(cleanup_results)
            
            # Cleanup dead letter queue
            await self._cleanup_deadletter_logs(cleanup_results)
            
            logger.info(f"Data cleanup completed: {cleanup_results}")
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
    
    async def _cleanup_audit_logs(self, results: Dict[str, Any]):
        """Clean up expired audit logs."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_policy.audit_retention_days)
        
        log_dir = self.audit_log_path.parent
        if not log_dir.exists():
            return
            
        for log_file in log_dir.glob("audit-*.jsonl"):
            try:
                # Extract date from filename
                date_str = log_file.stem.replace("audit-", "")
                file_date = datetime.fromisoformat(date_str)
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    results["audit_files_cleaned"] += 1
                    logger.info(f"Cleaned expired audit log: {log_file}")
                    
            except (ValueError, OSError) as e:
                logger.warning(f"Failed to process audit log {log_file}: {e}")


# Global data manager instance
data_manager = DataManager()


def get_data_manager() -> DataManager:
    """Get the global data manager instance."""
    return data_manager