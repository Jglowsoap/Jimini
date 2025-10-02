# app/forwarders/base.py
"""
Base forwarder with resilient error handling, retry logic, and circuit breaker integration.
"""

import time
import random
from typing import List, Dict, Any
from abc import ABC, abstractmethod

from app.circuit_breaker import circuit_manager, CircuitOpenError
from app.deadletter import deadletter_queue


class ResilientForwarder(ABC):
    """
    Base class for resilient forwarders with error handling and retry logic.
    """
    
    def __init__(self, name: str, max_retries: int = 2, base_delay: float = 0.1):
        self.name = name
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.circuit_breaker = circuit_manager.get_breaker(name)
    
    @abstractmethod
    def _send_batch(self, events: List[Dict[str, Any]]) -> None:
        """
        Send batch of events to target system.
        Implementation should raise exception on failure.
        """
        pass
    
    def send_many(self, events: List[Dict[str, Any]]) -> None:
        """
        Send events with resilient error handling, retries, and circuit breaker.
        """
        if not events:
            return
        
        try:
            # Use circuit breaker to protect against cascading failures
            self.circuit_breaker.call(self._send_with_retries, events)
            
        except CircuitOpenError:
            # Circuit is open, send directly to dead letter
            reason = f"Circuit breaker {self.name} is OPEN"
            deadletter_queue.write_many(self.name, events, reason)
            print(f"[{self.name}] Circuit open, {len(events)} events sent to dead letter")
            
        except Exception as e:
            # Final fallback - should not reach here due to retry logic
            reason = f"Unexpected error after retries: {str(e)}"
            deadletter_queue.write_many(self.name, events, reason, self.max_retries)
            print(f"[{self.name}] Final fallback: {len(events)} events sent to dead letter - {reason}")
    
    def _send_with_retries(self, events: List[Dict[str, Any]]) -> None:
        """Send events with retry logic and exponential backoff with jitter"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                self._send_batch(events)
                return  # Success
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calculate delay with exponential backoff and jitter
                    delay = self.base_delay * (2 ** attempt)
                    jitter = random.uniform(0.1, 0.3)
                    sleep_time = delay + jitter
                    
                    print(f"[{self.name}] Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                else:
                    # Final attempt failed, send to dead letter
                    reason = f"Failed after {self.max_retries + 1} attempts: {str(e)}"
                    deadletter_queue.write_many(self.name, events, reason, self.max_retries)
                    print(f"[{self.name}] All retries exhausted, {len(events)} events sent to dead letter")
                    
                    # Re-raise to trigger circuit breaker failure count
                    raise e
    
    def get_status(self) -> Dict[str, Any]:
        """Get forwarder status including circuit breaker state"""
        return {
            "name": self.name,
            "circuit_state": self.circuit_breaker.get_state(),
            "max_retries": self.max_retries,
            "base_delay": self.base_delay
        }