# tests/test_circuit_breaker_corrected.py - Comprehensive Circuit Breaker Tests

import pytest
import time
import threading
from unittest.mock import MagicMock, patch

from app.circuit_breaker import (
    CircuitBreaker, CircuitBreakerManager, CircuitOpenError,
    CircuitState, circuit_manager
)


class TestCircuitBreaker:
    """Test circuit breaker functionality and resilience."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization with default values."""
        cb = CircuitBreaker("test_service")
        
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60
        assert cb.get_state() == "closed"
        assert cb.metrics.failure_count == 0

    def test_circuit_breaker_custom_parameters(self):
        """Test circuit breaker with custom parameters."""
        cb = CircuitBreaker(
            "test_service",
            failure_threshold=3,
            recovery_timeout=30,
            test_requests_threshold=2
        )
        
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30
        assert cb.test_requests_threshold == 2

    def test_successful_execution_closed_state(self):
        """Test successful execution in CLOSED state."""
        cb = CircuitBreaker("test_service", failure_threshold=2)
        
        def successful_operation():
            return "success"
        
        result = cb.call(successful_operation)
        
        assert result == "success"
        assert cb.get_state() == "closed"
        assert cb.metrics.failure_count == 0

    def test_failure_execution_closed_state(self):
        """Test failure execution in CLOSED state."""
        cb = CircuitBreaker("test_service", failure_threshold=2)
        
        def failing_operation():
            raise ValueError("Operation failed")
        
        # First failure
        with pytest.raises(ValueError):
            cb.call(failing_operation)
        
        assert cb.get_state() == "closed"
        assert cb.metrics.failure_count == 1
        
        # Second failure should open circuit
        with pytest.raises(ValueError):
            cb.call(failing_operation)
        
        assert cb.get_state() == "open"
        assert cb.metrics.failure_count == 2

    def test_open_state_behavior(self):
        """Test circuit breaker behavior in OPEN state."""
        cb = CircuitBreaker("test_service", failure_threshold=1, recovery_timeout=1)
        
        # Trigger failure to open circuit
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("Failure")))
        
        assert cb.get_state() == "open"
        
        # Subsequent calls should fail fast
        with pytest.raises(CircuitOpenError, match="Circuit breaker test_service is OPEN"):
            cb.call(lambda: "should not execute")

    def test_half_open_state_successful_recovery(self):
        """Test successful recovery from HALF_OPEN state."""
        cb = CircuitBreaker("test_service", failure_threshold=1, recovery_timeout=0.1, test_requests_threshold=1)
        
        # Open the circuit
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("Failure")))
        
        assert cb.get_state() == "open"
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Next call should transition to HALF_OPEN and succeed
        result = cb.call(lambda: "success")
        
        assert result == "success"
        assert cb.get_state() == "closed"
        assert cb.metrics.failure_count == 0

    def test_circuit_breaker_force_operations(self):
        """Test manual circuit breaker open/close operations."""
        cb = CircuitBreaker("test_service", failure_threshold=1)
        
        # Force open the circuit
        cb.force_open()
        assert cb.get_state() == "open"
        
        # Force close the circuit breaker
        cb.force_close()
        assert cb.get_state() == "closed"
        assert cb.metrics.failure_count == 0

    def test_circuit_breaker_state_checks(self):
        """Test circuit breaker state checking methods."""
        cb = CircuitBreaker("test_service", failure_threshold=1)
        
        # Initially closed
        assert cb.is_closed() is True
        
        # Open the circuit
        cb.force_open()
        assert cb.is_closed() is False
        assert cb.get_state() == "open"
        
        # Close the circuit
        cb.force_close()
        assert cb.is_closed() is True
        assert cb.get_state() == "closed"


class TestCircuitBreakerManager:
    """Test circuit breaker manager functionality."""

    def test_manager_get_breaker(self):
        """Test getting circuit breaker by name."""
        manager = CircuitBreakerManager()
        
        cb1 = manager.get_breaker("test_service")
        cb2 = manager.get_breaker("test_service")
        
        # Should return the same instance
        assert cb1 is cb2
        assert cb1.name == "test_service"

    def test_different_circuit_breakers(self):
        """Test getting different circuit breakers."""
        manager = CircuitBreakerManager()
        
        cb1 = manager.get_breaker("service1")
        cb2 = manager.get_breaker("service2")
        
        assert cb1 is not cb2
        assert cb1.name == "service1"
        assert cb2.name == "service2"

    def test_get_all_states(self):
        """Test getting status of all circuit breakers."""
        manager = CircuitBreakerManager()
        
        # Create circuit breakers in different states
        cb1 = manager.get_breaker("service1", failure_threshold=1)
        cb2 = manager.get_breaker("service2")
        
        # Open one circuit
        cb1.force_open()
        
        states = manager.get_all_states()
        
        assert len(states) == 2
        assert states["service1"] == "open"
        assert states["service2"] == "closed"

    def test_are_all_closed(self):
        """Test checking if all circuit breakers are closed."""
        manager = CircuitBreakerManager()
        
        # Create circuit breakers
        cb1 = manager.get_breaker("service1")
        cb2 = manager.get_breaker("service2")
        
        # All should be closed initially
        assert manager.are_all_closed() is True
        
        # Open one circuit
        cb1.force_open()
        assert manager.are_all_closed() is False
        
        # Close it again
        cb1.force_close()
        assert manager.are_all_closed() is True


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration with other components."""

    @patch('app.forwarders.splunk_forwarder.SplunkForwarder.send_many')
    def test_circuit_breaker_with_forwarder(self, mock_send):
        """Test circuit breaker integration with forwarders."""
        cb = circuit_manager.get_breaker("splunk_forwarder", failure_threshold=2)
        
        # Simulate forwarder failures
        mock_send.side_effect = Exception("Connection failed")
        
        # First two failures should open the circuit
        for _ in range(2):
            try:
                cb.call(mock_send, [{"event": "test"}])
            except Exception:
                pass
        
        assert cb.get_state() == "open"
        
        # Next call should fail fast without calling forwarder
        mock_send.reset_mock()
        
        with pytest.raises(CircuitOpenError):
            cb.call(mock_send, [{"event": "test"}])
        
        # Forwarder should not have been called
        mock_send.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])