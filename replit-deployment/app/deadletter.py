# app/deadletter.py
"""
Dead letter queue for failed forwarder operations.
Stores events that couldn't be delivered for later replay.
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class DeadLetterEvent:
    """Dead letter event with retry information"""
    timestamp: str
    target: str
    reason: str
    retry_count: int
    original_event: Dict[str, Any]


class DeadLetterQueue:
    """Dead letter queue for failed events"""
    
    def __init__(self, file_path: str = "logs/deadletter.jsonl"):
        self.file_path = file_path
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure log directory exists"""
        log_dir = Path(self.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    def write_event(self, target: str, event: Dict[str, Any], reason: str, retry_count: int = 0):
        """Write single event to dead letter queue"""
        dead_event = DeadLetterEvent(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S+00:00Z", time.gmtime()),
            target=target,
            reason=reason,
            retry_count=retry_count,
            original_event=event
        )
        
        try:
            with open(self.file_path, "a") as f:
                f.write(json.dumps(asdict(dead_event)) + "\n")
        except Exception as e:
            # Fallback: log to stderr if can't write to file
            print(f"[deadletter] Failed to write dead letter: {e}")
    
    def write_many(self, target: str, events: List[Dict[str, Any]], reason: str, retry_count: int = 0):
        """Write multiple events to dead letter queue"""
        for event in events:
            self.write_event(target, event, reason, retry_count)
    
    def read_events(self, target: str = None) -> List[DeadLetterEvent]:
        """Read events from dead letter queue, optionally filtered by target"""
        if not os.path.exists(self.file_path):
            return []
        
        events = []
        try:
            with open(self.file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        event_data = json.loads(line)
                        event = DeadLetterEvent(**event_data)
                        
                        if target is None or event.target == target:
                            events.append(event)
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"[deadletter] Corrupted entry: {e}")
                        continue
        except Exception as e:
            print(f"[deadletter] Failed to read dead letter file: {e}")
        
        return events
    
    def clear_target(self, target: str):
        """Remove all events for a specific target (after successful replay)"""
        if not os.path.exists(self.file_path):
            return
        
        try:
            # Read all events
            all_events = []
            with open(self.file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        event_data = json.loads(line)
                        event = DeadLetterEvent(**event_data)
                        if event.target != target:
                            all_events.append(event)
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            # Rewrite file without the target's events
            with open(self.file_path, "w") as f:
                for event in all_events:
                    f.write(json.dumps(asdict(event)) + "\n")
                    
        except Exception as e:
            print(f"[deadletter] Failed to clear target {target}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dead letter queue statistics"""
        events = self.read_events()
        
        stats = {
            "total_events": len(events),
            "targets": {},
            "oldest_event": None,
            "newest_event": None
        }
        
        if events:
            # Group by target
            for event in events:
                target = event.target
                if target not in stats["targets"]:
                    stats["targets"][target] = 0
                stats["targets"][target] += 1
            
            # Find oldest and newest
            timestamps = [event.timestamp for event in events]
            stats["oldest_event"] = min(timestamps)
            stats["newest_event"] = max(timestamps)
        
        return stats


# Global instance
deadletter_queue = DeadLetterQueue()