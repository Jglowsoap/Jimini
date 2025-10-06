# app/decision_logs.py
"""
Decision Log Service for Jimini Policy Gateway

Handles querying and analysis of policy evaluation decisions.
Provides enhanced audit log querying capabilities for dashboard integration.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict

from app.models import (
    DecisionLogEntry,
    DecisionLogResponse, 
    DecisionStatsResponse,
    ShadowStatusResponse,
    ShadowDecisionEntry,
    ShadowDecisionsResponse
)
from app.audit_logger import get_audit_stats
from config.loader import get_current_config


class DecisionLogManager:
    """Service for querying and analyzing policy decisions"""
    
    def __init__(self):
        self.config = get_current_config()
        self.audit_file_path = self.config.siem.jsonl.file_path
        
    def query_decisions(self,
                       page: int = 1,
                       page_size: int = 50,
                       action_filter: Optional[str] = None,
                       rule_filter: Optional[str] = None,
                       endpoint_filter: Optional[str] = None,
                       start_time: Optional[str] = None,
                       end_time: Optional[str] = None,
                       search_text: Optional[str] = None) -> DecisionLogResponse:
        """Query decision logs with filtering and pagination"""
        
        # Read all decisions from audit log
        all_decisions = self._read_audit_decisions()
        
        # Apply filters
        filtered_decisions = self._apply_filters(
            all_decisions,
            action_filter=action_filter,
            rule_filter=rule_filter,
            endpoint_filter=endpoint_filter,
            start_time=start_time,
            end_time=end_time,
            search_text=search_text
        )
        
        # Sort by timestamp (newest first)
        filtered_decisions.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        total = len(filtered_decisions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_decisions = filtered_decisions[start_idx:end_idx]
        
        return DecisionLogResponse(
            decisions=paginated_decisions,
            total=total,
            page=page,
            page_size=page_size,
            has_next=end_idx < total,
            has_prev=page > 1
        )
    
    def get_decision_by_request_id(self, request_id: str) -> Optional[DecisionLogEntry]:
        """Get a specific decision by request ID"""
        
        all_decisions = self._read_audit_decisions()
        
        for decision in all_decisions:
            if decision.request_id == request_id:
                return decision
                
        return None
    
    def get_decision_stats(self, 
                          start_time: Optional[str] = None,
                          end_time: Optional[str] = None) -> DecisionStatsResponse:
        """Get aggregated decision statistics for a time range"""
        
        # Default to last 24 hours if no time range specified
        if not start_time:
            start_dt = datetime.utcnow() - timedelta(hours=24)
            start_time = start_dt.isoformat()
        
        if not end_time:
            end_time = datetime.utcnow().isoformat()
        
        # Get decisions in time range
        decisions = self._apply_filters(
            self._read_audit_decisions(),
            start_time=start_time,
            end_time=end_time
        )
        
        # Calculate statistics
        total_decisions = len(decisions)
        decisions_by_action = defaultdict(int)
        decisions_by_rule = defaultdict(int) 
        shadow_decisions = 0
        latencies = []
        endpoints = set()
        
        for decision in decisions:
            decisions_by_action[decision.action] += 1
            
            for rule_id in decision.rule_ids:
                decisions_by_rule[rule_id] += 1
            
            if decision.shadow_mode and decision.raw_decision != decision.action:
                shadow_decisions += 1
                
            if decision.latency_ms:
                latencies.append(decision.latency_ms)
                
            endpoints.add(decision.endpoint)
        
        # Calculate averages
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        
        # Calculate peak RPS (approximate)
        peak_rps = 0.0
        if decisions:
            # Group by minute and find peak
            minute_counts = defaultdict(int)
            for decision in decisions:
                # Truncate to minute
                dt = datetime.fromisoformat(decision.timestamp.rstrip('Z').replace('Z', '+00:00'))
                minute_key = dt.replace(second=0, microsecond=0)
                minute_counts[minute_key] += 1
            
            peak_rps = max(minute_counts.values()) / 60.0 if minute_counts else 0.0
        
        time_range_desc = f"{start_time} to {end_time}"
        
        return DecisionStatsResponse(
            time_range=time_range_desc,
            total_decisions=total_decisions,
            decisions_by_action=dict(decisions_by_action),
            decisions_by_rule=dict(decisions_by_rule),
            shadow_decisions=shadow_decisions,
            avg_latency_ms=avg_latency,
            peak_rps=peak_rps,
            unique_endpoints=len(endpoints)
        )
    
    def get_shadow_status(self) -> ShadowStatusResponse:
        """Get current shadow mode status and statistics"""
        
        config = get_current_config()
        shadow_enabled = config.app.shadow_mode
        
        # Get shadow decisions from today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_start = today.isoformat()
        
        decisions = self._apply_filters(
            self._read_audit_decisions(),
            start_time=today_start
        )
        
        shadow_decisions_today = 0
        would_have_blocked = 0
        would_have_flagged = 0
        total_decisions = len(decisions)
        
        for decision in decisions:
            if decision.shadow_mode and decision.raw_decision != decision.action:
                shadow_decisions_today += 1
                if decision.raw_decision == "block":
                    would_have_blocked += 1
                elif decision.raw_decision == "flag":
                    would_have_flagged += 1
        
        # Calculate effectiveness score
        effectiveness_score = None
        if total_decisions > 0:
            effectiveness_score = (shadow_decisions_today / total_decisions) * 100
        
        # Get override rules
        override_rules = getattr(config.app, 'shadow_overrides', [])
        
        return ShadowStatusResponse(
            enabled=shadow_enabled,
            override_rules=override_rules,
            shadow_decisions_today=shadow_decisions_today,
            would_have_blocked=would_have_blocked,
            would_have_flagged=would_have_flagged,
            effectiveness_score=effectiveness_score
        )
    
    def get_shadow_decisions(self,
                           page: int = 1,
                           page_size: int = 50,
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None) -> ShadowDecisionsResponse:
        """Get decisions that would have been different without shadow mode"""
        
        # Get all decisions
        all_decisions = self._apply_filters(
            self._read_audit_decisions(),
            start_time=start_time,
            end_time=end_time
        )
        
        # Filter for shadow decisions only
        shadow_decisions = []
        for decision in all_decisions:
            if (decision.shadow_mode and 
                decision.raw_decision and 
                decision.raw_decision != decision.action):
                
                shadow_entry = ShadowDecisionEntry(
                    request_id=decision.request_id,
                    timestamp=decision.timestamp,
                    original_decision=decision.action,
                    shadow_decision=decision.raw_decision,
                    rule_ids=decision.rule_ids,
                    endpoint=decision.endpoint,
                    text_excerpt=decision.text_excerpt
                )
                shadow_decisions.append(shadow_entry)
        
        # Sort by timestamp (newest first)
        shadow_decisions.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        total = len(shadow_decisions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_decisions = shadow_decisions[start_idx:end_idx]
        
        return ShadowDecisionsResponse(
            decisions=paginated_decisions,
            total=total,
            page=page,
            page_size=page_size,
            has_next=end_idx < total,
            has_prev=page > 1
        )
    
    def _read_audit_decisions(self) -> List[DecisionLogEntry]:
        """Read all audit decisions from JSONL file"""
        
        decisions = []
        
        if not os.path.exists(self.audit_file_path):
            return decisions
        
        try:
            with open(self.audit_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        
                        # Skip non-policy-decision entries (e.g., audit_initialized events)
                        if 'action' not in record:
                            continue
                        
                        # Convert audit record to decision log entry
                        decision = DecisionLogEntry(
                            request_id=record.get('request_id', ''),
                            timestamp=record.get('timestamp', ''),
                            action=record.get('action', ''),
                            rule_ids=record.get('rule_ids', []),
                            endpoint=record.get('endpoint', ''),
                            direction=record.get('direction', 'inbound'),
                            text_excerpt=record.get('text_excerpt'),
                            agent_id=record.get('metadata', {}).get('agent_id') if record.get('metadata') else None,
                            latency_ms=record.get('metadata', {}).get('latency_ms') if record.get('metadata') else None,
                            shadow_mode=record.get('metadata', {}).get('shadow_mode') if record.get('metadata') else None,
                            raw_decision=record.get('metadata', {}).get('raw_decision') if record.get('metadata') else None,
                            metadata=record.get('metadata', {}) if record.get('metadata') else {}
                        )
                        decisions.append(decision)
                        
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue
                        
        except Exception:
            # Return empty list if file can't be read
            pass
        
        return decisions
    
    def _apply_filters(self,
                      decisions: List[DecisionLogEntry],
                      action_filter: Optional[str] = None,
                      rule_filter: Optional[str] = None,
                      endpoint_filter: Optional[str] = None,
                      start_time: Optional[str] = None,
                      end_time: Optional[str] = None,
                      search_text: Optional[str] = None) -> List[DecisionLogEntry]:
        """Apply filters to decision list"""
        
        filtered = decisions
        
        # Action filter
        if action_filter:
            filtered = [d for d in filtered if d.action == action_filter]
        
        # Rule filter
        if rule_filter:
            filtered = [d for d in filtered if rule_filter in d.rule_ids]
        
        # Endpoint filter
        if endpoint_filter:
            filtered = [d for d in filtered if endpoint_filter in d.endpoint]
        
        # Time range filters
        if start_time:
            try:
                # Normalize timezone info: add +00:00 if no timezone present
                start_time_normalized = start_time
                if not ('+' in start_time[-6:] or start_time.endswith('Z')):
                    start_time_normalized = start_time + '+00:00'
                start_dt = datetime.fromisoformat(start_time_normalized.replace('Z', '+00:00'))
                
                filtered = [
                    d for d in filtered 
                    if datetime.fromisoformat(d.timestamp.rstrip('Z').replace('Z', '+00:00')) >= start_dt
                ]
            except (ValueError, AttributeError):
                pass  # Invalid date format, skip filter
        
        if end_time:
            try:
                # Normalize timezone info: add +00:00 if no timezone present
                end_time_normalized = end_time
                if not ('+' in end_time[-6:] or end_time.endswith('Z')):
                    end_time_normalized = end_time + '+00:00'
                end_dt = datetime.fromisoformat(end_time_normalized.replace('Z', '+00:00'))
                
                filtered = [
                    d for d in filtered 
                    if datetime.fromisoformat(d.timestamp.rstrip('Z').replace('Z', '+00:00')) <= end_dt
                ]
            except (ValueError, AttributeError):
                pass  # Invalid date format, skip filter
        
        # Text search
        if search_text:
            search_lower = search_text.lower()
            filtered = [
                d for d in filtered 
                if (d.text_excerpt and search_lower in d.text_excerpt.lower()) or
                   search_lower in d.endpoint.lower() or
                   any(search_lower in rule_id.lower() for rule_id in d.rule_ids)
            ]
        
        return filtered


# Global decision log manager instance
_decision_log_manager: Optional[DecisionLogManager] = None


def get_decision_log_manager() -> DecisionLogManager:
    """Get the global decision log manager instance"""
    global _decision_log_manager
    if _decision_log_manager is None:
        _decision_log_manager = DecisionLogManager()
    return _decision_log_manager