# app/circuit_breaker.py
"""
Circuit breaker implementation for resilient forwarder operations.
Implements fail-fast pattern with automatic recovery.
"""

import time
import threading
from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitMetrics:
    """Circuit breaker metrics"""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    state: CircuitState = CircuitState.CLOSED


class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    Opens circuit after consecutive failures, preventing cascading failures.
    Automatically attempts recovery after timeout period.
    """
    
    def __init__(
        self, 
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        test_requests_threshold: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.test_requests_threshold = test_requests_threshold
        
        self.metrics = CircuitMetrics()
        self.lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self.lock:
            if self._should_reject():
                raise CircuitOpenError(f"Circuit breaker {self.name} is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result
            except Exception as e:
                self._record_failure()
                raise e
    
    def _should_reject(self) -> bool:
        """Check if request should be rejected based on circuit state"""
        if self.metrics.state == CircuitState.CLOSED:
            return False
        
        if self.metrics.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (self.metrics.last_failure_time and 
                time.time() - self.metrics.last_failure_time > self.recovery_timeout):
                self.metrics.state = CircuitState.HALF_OPEN
                return False
            return True
        
        if self.metrics.state == CircuitState.HALF_OPEN:
            # Allow limited test requests
            return self.metrics.success_count >= self.test_requests_threshold
        
        return False
    
    def _record_success(self):
        """Record successful operation"""
        self.metrics.success_count += 1
        
        if self.metrics.state == CircuitState.HALF_OPEN:
            if self.metrics.success_count >= self.test_requests_threshold:
                self._close_circuit()
    
    def _record_failure(self):
        """Record failed operation"""
        self.metrics.failure_count += 1
        self.metrics.last_failure_time = time.time()
        
        if (self.metrics.state == CircuitState.CLOSED and 
            self.metrics.failure_count >= self.failure_threshold):
            self._open_circuit()
        elif self.metrics.state == CircuitState.HALF_OPEN:
            self._open_circuit()
    
    def _open_circuit(self):
        """Open circuit breaker"""
        self.metrics.state = CircuitState.OPEN
        self.metrics.success_count = 0
        print(f"[circuit_breaker] {self.name} circuit OPENED after {self.metrics.failure_count} failures")
    
    def _close_circuit(self):
        """Close circuit breaker"""
        self.metrics.state = CircuitState.CLOSED
        self.metrics.failure_count = 0
        self.metrics.success_count = 0
        print(f"[circuit_breaker] {self.name} circuit CLOSED - recovered")
    
    def get_state(self) -> str:
        """Get current circuit state"""
        return self.metrics.state.value
    
    def is_closed(self) -> bool:
        """Check if circuit is closed (healthy)"""
        return self.metrics.state == CircuitState.CLOSED
    
    def force_open(self):
        """Manually open circuit (for testing)"""
        with self.lock:
            self._open_circuit()
    
    def force_close(self):
        """Manually close circuit (for testing)"""
        with self.lock:
            self._close_circuit()


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreakerManager:
    """Global circuit breaker manager"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.Lock()
    
    def get_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, **kwargs)
            return self.breakers[name]
    
    def get_all_states(self) -> Dict[str, str]:
        """Get states of all circuit breakers"""
        with self.lock:
            return {name: breaker.get_state() for name, breaker in self.breakers.items()}
    
    def are_all_closed(self) -> bool:
        """Check if all circuit breakers are closed"""
        with self.lock:
            return all(breaker.is_closed() for breaker in self.breakers.values())


# Global instance
circuit_manager = CircuitBreakerManager()