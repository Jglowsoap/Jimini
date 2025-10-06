"""
Policy Approval Workflow Service

Handles policy approval workflows for enterprise compliance.
Provides approval tracking, role-based approvals, and audit trails.
"""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

import yaml
from pydantic import BaseModel


class ApprovalStatus(str, Enum):
    """Policy approval statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalType(str, Enum):
    """Types of policy approvals."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ENABLE = "enable"
    DISABLE = "disable"


@dataclass
class PolicyApprovalRequest:
    """Policy approval request data."""
    request_id: str
    rule_id: str
    approval_type: ApprovalType
    rule_data: Dict[str, Any]
    original_rule_data: Optional[Dict[str, Any]]
    requested_by: str
    requested_at: datetime
    expires_at: datetime
    justification: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class PolicyApprovalManager:
    """Manages policy approval workflows."""
    
    def __init__(self, approval_store_path: str = "data/approvals.json", 
                 approval_expiry_hours: int = 72):
        """Initialize policy approval manager.
        
        Args:
            approval_store_path: Path to store approval requests
            approval_expiry_hours: Hours until approval requests expire
        """
        self.approval_store_path = approval_store_path
        self.approval_expiry_hours = approval_expiry_hours
        self._ensure_approval_store()
        
    def _ensure_approval_store(self):
        """Ensure approval store directory exists."""
        store_dir = Path(self.approval_store_path).parent
        store_dir.mkdir(parents=True, exist_ok=True)
        
        if not Path(self.approval_store_path).exists():
            with open(self.approval_store_path, 'w') as f:
                json.dump({}, f)
    
    def _load_approvals(self) -> Dict[str, Dict]:
        """Load approval requests from storage."""
        try:
            with open(self.approval_store_path, 'r') as f:
                data = json.load(f)
                
            # Convert datetime strings back to datetime objects
            for approval_id, approval in data.items():
                approval['requested_at'] = datetime.fromisoformat(approval['requested_at'])
                approval['expires_at'] = datetime.fromisoformat(approval['expires_at'])
                if approval.get('approved_at'):
                    approval['approved_at'] = datetime.fromisoformat(approval['approved_at'])
                    
            return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_approvals(self, approvals: Dict[str, Dict]):
        """Save approval requests to storage."""
        # Convert datetime objects to strings for JSON serialization
        serializable_approvals = {}
        for approval_id, approval in approvals.items():
            serializable = approval.copy()
            serializable['requested_at'] = approval['requested_at'].isoformat()
            serializable['expires_at'] = approval['expires_at'].isoformat()
            if approval.get('approved_at'):
                serializable['approved_at'] = approval['approved_at'].isoformat()
            serializable_approvals[approval_id] = serializable
            
        with open(self.approval_store_path, 'w') as f:
            json.dump(serializable_approvals, f, indent=2)
    
    def create_approval_request(self, 
                              rule_id: str,
                              approval_type: ApprovalType,
                              rule_data: Dict[str, Any],
                              requested_by: str,
                              justification: str,
                              original_rule_data: Optional[Dict[str, Any]] = None) -> str:
        """Create a new policy approval request.
        
        Args:
            rule_id: ID of the rule to be modified
            approval_type: Type of approval (create, update, delete, etc.)
            rule_data: New rule data
            requested_by: User requesting the approval
            justification: Justification for the change
            original_rule_data: Current rule data (for updates/deletes)
            
        Returns:
            The approval request ID
        """
        request_id = f"approval_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.approval_expiry_hours)
        
        approval_request = PolicyApprovalRequest(
            request_id=request_id,
            rule_id=rule_id,
            approval_type=approval_type,
            rule_data=rule_data,
            original_rule_data=original_rule_data,
            requested_by=requested_by,
            requested_at=now,
            expires_at=expires_at,
            justification=justification
        )
        
        approvals = self._load_approvals()
        approvals[request_id] = asdict(approval_request)
        self._save_approvals(approvals)
        
        return request_id
    
    def get_approval_request(self, request_id: str) -> Optional[PolicyApprovalRequest]:
        """Get an approval request by ID."""
        approvals = self._load_approvals()
        approval_data = approvals.get(request_id)
        
        if not approval_data:
            return None
            
        return PolicyApprovalRequest(**approval_data)
    
    def list_approval_requests(self, 
                             status_filter: Optional[ApprovalStatus] = None,
                             requested_by: Optional[str] = None,
                             page: int = 1,
                             page_size: int = 50) -> Dict[str, Any]:
        """List approval requests with filtering and pagination.
        
        Args:
            status_filter: Filter by approval status
            requested_by: Filter by requesting user
            page: Page number (1-based)
            page_size: Items per page
            
        Returns:
            Paginated approval requests
        """
        approvals = self._load_approvals()
        
        # Convert to PolicyApprovalRequest objects and filter
        approval_requests = []
        for approval_id, approval_data in approvals.items():
            approval_request = PolicyApprovalRequest(**approval_data)
            
            # Update expired requests
            if (approval_request.status == ApprovalStatus.PENDING and 
                datetime.now(timezone.utc) > approval_request.expires_at):
                approval_request.status = ApprovalStatus.EXPIRED
                approvals[approval_id]['status'] = ApprovalStatus.EXPIRED
            
            # Apply filters
            if status_filter and approval_request.status != status_filter:
                continue
            if requested_by and approval_request.requested_by != requested_by:
                continue
                
            approval_requests.append(approval_request)
        
        # Save any status updates
        self._save_approvals(approvals)
        
        # Sort by requested_at descending
        approval_requests.sort(key=lambda x: x.requested_at, reverse=True)
        
        # Paginate
        total = len(approval_requests)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_requests = approval_requests[start_idx:end_idx]
        
        return {
            "requests": [asdict(req) for req in paginated_requests],
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_next": end_idx < total,
            "has_prev": page > 1
        }
    
    def approve_request(self, request_id: str, approved_by: str) -> bool:
        """Approve a policy request.
        
        Args:
            request_id: Approval request ID
            approved_by: User approving the request
            
        Returns:
            True if approved successfully, False otherwise
        """
        approvals = self._load_approvals()
        
        if request_id not in approvals:
            raise ValueError(f"Approval request {request_id} not found")
        
        approval = approvals[request_id]
        
        # Check if request is still pending
        if approval['status'] != ApprovalStatus.PENDING:
            raise ValueError(f"Request {request_id} is not pending (status: {approval['status']})")
        
        # Check if expired
        expires_at = datetime.fromisoformat(approval['expires_at'])
        if datetime.now(timezone.utc) > expires_at:
            approval['status'] = ApprovalStatus.EXPIRED
            self._save_approvals(approvals)
            raise ValueError(f"Request {request_id} has expired")
        
        # Approve the request
        approval['status'] = ApprovalStatus.APPROVED
        approval['approved_by'] = approved_by
        approval['approved_at'] = datetime.now(timezone.utc)
        
        self._save_approvals(approvals)
        return True
    
    def reject_request(self, request_id: str, rejected_by: str, reason: str) -> bool:
        """Reject a policy request.
        
        Args:
            request_id: Approval request ID
            rejected_by: User rejecting the request
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully, False otherwise
        """
        approvals = self._load_approvals()
        
        if request_id not in approvals:
            raise ValueError(f"Approval request {request_id} not found")
        
        approval = approvals[request_id]
        
        # Check if request is still pending
        if approval['status'] != ApprovalStatus.PENDING:
            raise ValueError(f"Request {request_id} is not pending (status: {approval['status']})")
        
        # Reject the request
        approval['status'] = ApprovalStatus.REJECTED
        approval['approved_by'] = rejected_by
        approval['approved_at'] = datetime.now(timezone.utc)
        approval['rejection_reason'] = reason
        
        self._save_approvals(approvals)
        return True
    
    def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval statistics."""
        approvals = self._load_approvals()
        
        stats = {
            "total_requests": len(approvals),
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "expired": 0,
            "avg_approval_time_hours": 0,
            "pending_by_type": {},
            "recent_activity": []
        }
        
        approval_times = []
        recent_limit = 10
        recent_requests = []
        
        now = datetime.now(timezone.utc)
        
        for approval_data in approvals.values():
            status = approval_data['status']
            approval_type = approval_data['approval_type']
            
            # Update expired requests
            if (status == ApprovalStatus.PENDING and 
                now > datetime.fromisoformat(approval_data['expires_at'])):
                status = ApprovalStatus.EXPIRED
                approval_data['status'] = ApprovalStatus.EXPIRED
            
            stats[status.lower()] += 1
            
            # Count pending by type
            if status == ApprovalStatus.PENDING:
                stats["pending_by_type"][approval_type] = stats["pending_by_type"].get(approval_type, 0) + 1
            
            # Calculate approval times
            if approval_data.get('approved_at'):
                requested_at = datetime.fromisoformat(approval_data['requested_at'])
                approved_at = datetime.fromisoformat(approval_data['approved_at'])
                approval_time = (approved_at - requested_at).total_seconds() / 3600
                approval_times.append(approval_time)
            
            # Collect recent activity
            recent_requests.append({
                "request_id": approval_data['request_id'],
                "rule_id": approval_data['rule_id'],
                "type": approval_type,
                "status": status,
                "requested_by": approval_data['requested_by'],
                "requested_at": approval_data['requested_at']
            })
        
        # Calculate average approval time
        if approval_times:
            stats["avg_approval_time_hours"] = sum(approval_times) / len(approval_times)
        
        # Sort and limit recent activity
        recent_requests.sort(key=lambda x: x['requested_at'], reverse=True)
        stats["recent_activity"] = recent_requests[:recent_limit]
        
        # Save any status updates (for expired requests)
        self._save_approvals(approvals)
        
        return stats


# Global instance
_approval_manager: Optional[PolicyApprovalManager] = None


def get_approval_manager() -> PolicyApprovalManager:
    """Get global policy approval manager instance."""
    global _approval_manager
    
    if _approval_manager is None:
        approval_store_path = os.getenv("JIMINI_APPROVAL_STORE", "data/approvals.json")
        approval_expiry_hours = int(os.getenv("JIMINI_APPROVAL_EXPIRY_HOURS", "72"))
        _approval_manager = PolicyApprovalManager(
            approval_store_path=approval_store_path,
            approval_expiry_hours=approval_expiry_hours
        )
    
    return _approval_manager