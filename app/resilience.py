"""
Enhanced error handling and resilience middleware for Jimini.
Implements circuit breakers, retry logic, graceful degradation, and proper error responses.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: int = 60  # Seconds before trying half-open
    success_threshold: int = 3  # Successes in half-open before closing
    timeout: float = 30.0  # Request timeout


@dataclass
class CircuitBreakerState:
    """Circuit breaker runtime state"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None


class CircuitBreaker:
    """Circuit breaker implementation with exponential backoff"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState()
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        async with self._lock:
            # Check if circuit is open
            if self.state.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' moving to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            await self._on_success()
            return result
            
        except Exception as e:
            await self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.state.last_failure_time:
            return True
        
        elapsed = datetime.now() - self.state.last_failure_time
        return elapsed.total_seconds() >= self.config.recovery_timeout
    
    async def _on_success(self):
        """Handle successful execution"""
        async with self._lock:
            self.state.last_success_time = datetime.now()
            
            if self.state.state == CircuitState.HALF_OPEN:
                self.state.success_count += 1
                if self.state.success_count >= self.config.success_threshold:
                    self.state.state = CircuitState.CLOSED
                    self.state.failure_count = 0
                    self.state.success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' CLOSED after recovery")
            elif self.state.state == CircuitState.CLOSED:
                self.state.failure_count = 0  # Reset failure count on success
    
    async def _on_failure(self):
        """Handle failed execution"""
        async with self._lock:
            self.state.last_failure_time = datetime.now()
            self.state.failure_count += 1
            
            if self.state.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN]:
                if self.state.failure_count >= self.config.failure_threshold:
                    self.state.state = CircuitState.OPEN
                    self.state.success_count = 0
                    logger.warning(f"Circuit breaker '{self.name}' OPENED after {self.state.failure_count} failures")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state for monitoring"""
        return {
            "name": self.name,
            "state": self.state.state.value,
            "failure_count": self.state.failure_count,
            "success_count": self.state.success_count,
            "last_failure": self.state.last_failure_time.isoformat() if self.state.last_failure_time else None,
            "last_success": self.state.last_success_time.isoformat() if self.state.last_success_time else None,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class RetryConfig:
    """Retry configuration with exponential backoff"""
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


async def retry_with_backoff(
    func: Callable,
    config: RetryConfig,
    retryable_exceptions: tuple = (Exception,),
    *args,
    **kwargs
):
    """Retry function with exponential backoff"""
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt == config.max_attempts - 1:
                # Last attempt, re-raise
                raise
            
            # Calculate delay with exponential backoff
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            # Add jitter to prevent thundering herd
            if config.jitter:
                import random
                delay = delay * (0.5 + random.random() * 0.5)
            
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
            await asyncio.sleep(delay)
    
    # Should not reach here, but just in case
    if last_exception:
        raise last_exception


class DeadLetterQueue:
    """Simple in-memory dead letter queue for failed operations"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.messages: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
    
    async def add_message(self, operation: str, payload: Dict[str, Any], error: str):
        """Add failed message to dead letter queue"""
        async with self._lock:
            message = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "payload": payload,
                "error": error,
                "retry_count": payload.get("retry_count", 0)
            }
            
            self.messages.append(message)
            
            # Maintain size limit
            if len(self.messages) > self.max_size:
                self.messages = self.messages[-self.max_size:]
            
            logger.error(f"Added message to dead letter queue: {operation} - {error}")
    
    async def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages from dead letter queue"""
        async with self._lock:
            if limit:
                return self.messages[-limit:]
            return self.messages.copy()
    
    async def clear(self):
        """Clear all messages from dead letter queue"""
        async with self._lock:
            count = len(self.messages)
            self.messages.clear()
            logger.info(f"Cleared {count} messages from dead letter queue")


class ResilienceManager:
    """Manages circuit breakers, retry logic, and dead letter queue"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.dead_letter_queue = DeadLetterQueue()
        self.default_retry_config = RetryConfig()
        self._setup_default_breakers()
    
    def _setup_default_breakers(self):
        """Setup default circuit breakers for external services"""
        services = [
            ("openai", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30)),
            ("slack", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60)),
            ("teams", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60)),
            ("splunk", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=120)),
            ("elastic", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=120)),
            ("otel", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30)),
        ]
        
        for name, config in services:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(
                name, CircuitBreakerConfig()
            )
        return self.circuit_breakers[name]
    
    async def execute_with_resilience(
        self,
        operation: str,
        func: Callable,
        payload: Optional[Dict[str, Any]] = None,
        retry_config: Optional[RetryConfig] = None,
        use_circuit_breaker: bool = True,
        *args,
        **kwargs
    ):
        """Execute function with full resilience (circuit breaker + retry + DLQ)"""
        retry_config = retry_config or self.default_retry_config
        payload = payload or {}
        
        async def _execute():
            if use_circuit_breaker:
                circuit_breaker = self.get_circuit_breaker(operation)
                return await circuit_breaker.call(func, *args, **kwargs)
            else:
                return await func(*args, **kwargs)
        
        try:
            return await retry_with_backoff(
                _execute,
                retry_config,
                retryable_exceptions=(CircuitBreakerOpenError, asyncio.TimeoutError, ConnectionError)
            )
        except Exception as e:
            # Add to dead letter queue
            await self.dead_letter_queue.add_message(
                operation=operation,
                payload=payload,
                error=str(e)
            )
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all circuit breakers"""
        return {
            "circuit_breakers": {
                name: breaker.get_state()
                for name, breaker in self.circuit_breakers.items()
            },
            "dead_letter_queue": {
                "size": len(self.dead_letter_queue.messages),
                "max_size": self.dead_letter_queue.max_size
            }
        }


# Global resilience manager instance
resilience_manager = ResilienceManager()


async def graceful_error_handler(request: Request, call_next):
    """Middleware for graceful error handling"""
    try:
        response = await call_next(request)
        return response
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.exception(f"Unhandled error in {request.method} {request.url}")
        
        # Return structured error response
        error_response = {
            "error": "internal_server_error",
            "message": "An internal server error occurred",
            "request_id": getattr(request.state, "request_id", None),
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create standardized error response"""
    response_data = {
        "error": error_code,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        response_data["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


# Common error responses
class ErrorResponses:
    """Standardized error responses"""
    
    @staticmethod
    def unauthorized(message: str = "Invalid API key") -> JSONResponse:
        return create_error_response("unauthorized", message, 401)
    
    @staticmethod
    def forbidden(message: str = "Access denied") -> JSONResponse:
        return create_error_response("forbidden", message, 403)
    
    @staticmethod
    def not_found(message: str = "Resource not found") -> JSONResponse:
        return create_error_response("not_found", message, 404)
    
    @staticmethod
    def rate_limited(message: str = "Rate limit exceeded") -> JSONResponse:
        return create_error_response("rate_limited", message, 429)
    
    @staticmethod
    def validation_error(message: str, details: Dict[str, Any] = None) -> JSONResponse:
        return create_error_response("validation_error", message, 400, details)
    
    @staticmethod
    def service_unavailable(service: str, message: str = None) -> JSONResponse:
        message = message or f"Service {service} is temporarily unavailable"
        return create_error_response("service_unavailable", message, 503, {"service": service})
    
    @staticmethod
    def internal_error(message: str = "Internal server error") -> JSONResponse:
        return create_error_response("internal_server_error", message, 500)