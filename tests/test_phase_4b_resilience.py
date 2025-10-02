"""
Test Phase 4B: Error Handling & Resilience
Tests circuit breakers, retry logic, dead letter queue, and error responses.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError,
    RetryConfig,
    retry_with_backoff,
    DeadLetterQueue,
    ResilienceManager,
    ErrorResponses,
    graceful_error_handler
)


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @pytest.fixture
    def circuit_breaker(self):
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=1,  # Short for testing
            success_threshold=2,
            timeout=0.5
        )
        return CircuitBreaker("test_service", config)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_normal_operation(self, circuit_breaker):
        """Test circuit breaker in normal closed state"""
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state.state == CircuitState.CLOSED
        assert circuit_breaker.state.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self, circuit_breaker):
        """Test circuit breaker opens after failure threshold"""
        async def failure_func():
            raise Exception("Service error")
        
        # First failure
        with pytest.raises(Exception):
            await circuit_breaker.call(failure_func)
        assert circuit_breaker.state.state == CircuitState.CLOSED
        assert circuit_breaker.state.failure_count == 1
        
        # Second failure - should open circuit
        with pytest.raises(Exception):
            await circuit_breaker.call(failure_func)
        assert circuit_breaker.state.state == CircuitState.OPEN
        assert circuit_breaker.state.failure_count == 2
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self, circuit_breaker):
        """Test circuit breaker blocks requests when open"""
        async def failure_func():
            raise Exception("Service error")
        
        # Trigger circuit opening
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit_breaker.call(failure_func)
        
        assert circuit_breaker.state.state == CircuitState.OPEN
        
        # Should block further requests
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call(lambda: "success")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self, circuit_breaker):
        """Test circuit breaker half-open state and recovery"""
        async def failure_func():
            raise Exception("Service error")
        
        async def success_func():
            return "success"
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit_breaker.call(failure_func)
        
        assert circuit_breaker.state.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # First call should move to half-open
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state.state == CircuitState.HALF_OPEN
        assert circuit_breaker.state.success_count == 1
        
        # Second success should close the circuit
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state.state == CircuitState.CLOSED
        assert circuit_breaker.state.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_timeout(self, circuit_breaker):
        """Test circuit breaker timeout functionality"""
        async def slow_func():
            await asyncio.sleep(1.0)  # Longer than timeout
            return "success"
        
        with pytest.raises(asyncio.TimeoutError):
            await circuit_breaker.call(slow_func)
        
        assert circuit_breaker.state.failure_count == 1


class TestRetryLogic:
    """Test retry logic with exponential backoff"""
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test successful execution on first attempt"""
        call_count = 0
        
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        config = RetryConfig(max_attempts=3, base_delay=0.1)
        result = await retry_with_backoff(success_func, config)
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test successful execution after initial failures"""
        call_count = 0
        
        async def eventually_success_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        start_time = time.time()
        result = await retry_with_backoff(
            eventually_success_func, 
            config, 
            retryable_exceptions=(ConnectionError,)
        )
        elapsed = time.time() - start_time
        
        assert result == "success"
        assert call_count == 3
        assert elapsed >= 0.01  # Should have some delay
    
    @pytest.mark.asyncio
    async def test_retry_exhausts_attempts(self):
        """Test retry exhaustion when all attempts fail"""
        call_count = 0
        
        async def always_fail_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent failure")
        
        config = RetryConfig(max_attempts=2, base_delay=0.01)
        
        with pytest.raises(ConnectionError, match="Persistent failure"):
            await retry_with_backoff(
                always_fail_func, 
                config,
                retryable_exceptions=(ConnectionError,)
            )
        
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_non_retryable_exception(self):
        """Test that non-retryable exceptions are not retried"""
        call_count = 0
        
        async def non_retryable_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")
        
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        
        with pytest.raises(ValueError, match="Not retryable"):
            await retry_with_backoff(
                non_retryable_func,
                config,
                retryable_exceptions=(ConnectionError,)
            )
        
        assert call_count == 1  # Should not retry


class TestDeadLetterQueue:
    """Test dead letter queue functionality"""
    
    @pytest.fixture
    def dlq(self):
        return DeadLetterQueue(max_size=3)
    
    @pytest.mark.asyncio
    async def test_add_message_to_dlq(self, dlq):
        """Test adding messages to dead letter queue"""
        await dlq.add_message("test_op", {"data": "test"}, "Test error")
        
        messages = await dlq.get_messages()
        assert len(messages) == 1
        
        message = messages[0]
        assert message["operation"] == "test_op"
        assert message["payload"]["data"] == "test"
        assert message["error"] == "Test error"
        assert "timestamp" in message
    
    @pytest.mark.asyncio
    async def test_dlq_size_limit(self, dlq):
        """Test dead letter queue respects size limit"""
        # Add more messages than max_size
        for i in range(5):
            await dlq.add_message(f"op_{i}", {"index": i}, f"Error {i}")
        
        messages = await dlq.get_messages()
        assert len(messages) == 3  # Should keep only last 3
        
        # Should have messages 2, 3, 4 (0-indexed)
        assert messages[0]["payload"]["index"] == 2
        assert messages[1]["payload"]["index"] == 3
        assert messages[2]["payload"]["index"] == 4
    
    @pytest.mark.asyncio
    async def test_dlq_get_with_limit(self, dlq):
        """Test getting limited number of messages"""
        for i in range(3):
            await dlq.add_message(f"op_{i}", {"index": i}, f"Error {i}")
        
        messages = await dlq.get_messages(limit=2)
        assert len(messages) == 2
        # Should get last 2 messages
        assert messages[0]["payload"]["index"] == 1
        assert messages[1]["payload"]["index"] == 2
    
    @pytest.mark.asyncio
    async def test_dlq_clear(self, dlq):
        """Test clearing dead letter queue"""
        await dlq.add_message("test", {}, "error")
        messages = await dlq.get_messages()
        assert len(messages) == 1
        
        await dlq.clear()
        messages = await dlq.get_messages()
        assert len(messages) == 0


class TestResilienceManager:
    """Test resilience manager integration"""
    
    @pytest.fixture
    def manager(self):
        return ResilienceManager()
    
    @pytest.mark.asyncio
    async def test_execute_with_resilience_success(self, manager):
        """Test successful execution through resilience manager"""
        call_count = 0
        
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await manager.execute_with_resilience(
            operation="test_service",
            func=success_func,
            payload={"test": "data"}
        )
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_resilience_failure_to_dlq(self, manager):
        """Test failed execution goes to dead letter queue"""
        async def failure_func():
            raise Exception("Service unavailable")
        
        with pytest.raises(Exception, match="Service unavailable"):
            await manager.execute_with_resilience(
                operation="test_service",
                func=failure_func,
                payload={"test": "data"},
                use_circuit_breaker=False  # Disable CB for this test
            )
        
        # Check dead letter queue
        messages = await manager.dead_letter_queue.get_messages()
        assert len(messages) == 1
        
        message = messages[0]
        assert message["operation"] == "test_service"
        assert message["payload"]["test"] == "data"
        assert "Service unavailable" in message["error"]
    
    def test_get_health_status(self, manager):
        """Test health status reporting"""
        health = manager.get_health_status()
        
        assert "circuit_breakers" in health
        assert "dead_letter_queue" in health
        
        # Should have default circuit breakers
        assert "openai" in health["circuit_breakers"]
        assert "slack" in health["circuit_breakers"]
        
        dlq_info = health["dead_letter_queue"]
        assert "size" in dlq_info
        assert "max_size" in dlq_info


class TestErrorResponses:
    """Test standardized error responses"""
    
    def test_unauthorized_response(self):
        """Test unauthorized error response"""
        response = ErrorResponses.unauthorized("Custom message")
        
        assert response.status_code == 401
        content = response.body.decode()
        assert "unauthorized" in content
        assert "Custom message" in content
    
    def test_validation_error_with_details(self):
        """Test validation error with details"""
        details = {"field": "api_key", "issue": "missing"}
        response = ErrorResponses.validation_error("Validation failed", details)
        
        assert response.status_code == 400
        content = response.body.decode()
        assert "validation_error" in content
        assert "Validation failed" in content
        assert "api_key" in content
    
    def test_service_unavailable(self):
        """Test service unavailable response"""
        response = ErrorResponses.service_unavailable("openai")
        
        assert response.status_code == 503
        content = response.body.decode()
        assert "service_unavailable" in content
        assert "openai" in content


@pytest.mark.asyncio
async def test_integration_circuit_breaker_with_retry():
    """Test integration of circuit breaker with retry logic"""
    manager = ResilienceManager()
    call_count = 0
    
    async def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise ConnectionError("Temporary failure")
        return "success"
    
    # Configure shorter timeouts for testing
    retry_config = RetryConfig(max_attempts=3, base_delay=0.01)
    
    result = await manager.execute_with_resilience(
        operation="integration_test",
        func=failing_func,
        retry_config=retry_config,
        use_circuit_breaker=False  # Test retry without CB interference
    )
    
    assert result == "success"
    assert call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])