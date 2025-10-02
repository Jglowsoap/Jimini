"""
Security middleware for HTTP security headers and input validation.
Implements OWASP recommended security headers and request sanitization.
"""

import re
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Set, Callable, Any
from urllib.parse import unquote

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    def __init__(self, app, config: Dict[str, Any] = None):
        super().__init__(app)
        self.config = config or {}
        
        # Default security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self'; "
                "font-src 'self'; "
                "object-src 'none'; "
                "media-src 'self'; "
                "frame-src 'none';"
            ),
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            )
        }
        
        # Override with config if provided
        if "security_headers" in self.config:
            self.security_headers.update(self.config["security_headers"])
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers to response
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for input validation and sanitization"""
    
    def __init__(self, app, config: Dict[str, Any] = None):
        super().__init__(app)
        self.config = config or {}
        
        # Maximum request sizes
        self.max_json_size = self.config.get("max_json_size", 10 * 1024 * 1024)  # 10MB
        self.max_form_size = self.config.get("max_form_size", 1 * 1024 * 1024)   # 1MB
        self.max_text_length = self.config.get("max_text_length", 1 * 1024 * 1024)  # 1MB
        
        # Dangerous patterns to detect
        self.dangerous_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'vbscript:', re.IGNORECASE),
            re.compile(r'onload=', re.IGNORECASE),
            re.compile(r'onerror=', re.IGNORECASE),
            re.compile(r'onclick=', re.IGNORECASE),
            re.compile(r'eval\s*\(', re.IGNORECASE),
            re.compile(r'expression\s*\(', re.IGNORECASE),
            # SQL injection patterns
            re.compile(r"(?:(?:union.*?select)|(?:select.*?from)|(?:insert.*?into)|(?:delete.*?from)|(?:drop.*?table))", re.IGNORECASE),
            re.compile(r"(?:(?:'|\").*?(?:or|and).*?(?:'|\")\s*=\s*(?:'|\").*?(?:'|\"))", re.IGNORECASE),
            # Command injection patterns
            re.compile(r'[;&|`$(){}[\]<>].*?(?:rm|cat|ls|ps|kill|chmod|sudo|su|wget|curl)', re.IGNORECASE),
            re.compile(r'(?:\$\(|\`|%[0-9a-f]{2})', re.IGNORECASE),
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            re.compile(r'\.\./', re.IGNORECASE),
            re.compile(r'\.\.\\', re.IGNORECASE),
            re.compile(r'%2e%2e%2f', re.IGNORECASE),
            re.compile(r'%2e%2e%5c', re.IGNORECASE),
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length:
            size = int(content_length)
            content_type = request.headers.get("content-type", "").lower()
            
            if "json" in content_type and size > self.max_json_size:
                return JSONResponse(
                    status_code=413,
                    content={"error": "payload_too_large", "message": "JSON payload exceeds maximum size"}
                )
            elif "form" in content_type and size > self.max_form_size:
                return JSONResponse(
                    status_code=413,
                    content={"error": "payload_too_large", "message": "Form payload exceeds maximum size"}
                )
        
        # Validate URL for path traversal
        url_path = unquote(str(request.url.path))
        for pattern in self.path_traversal_patterns:
            if pattern.search(url_path):
                return JSONResponse(
                    status_code=400,
                    content={"error": "invalid_path", "message": "Invalid path detected"}
                )
        
        # Process request normally
        response = await call_next(request)
        return response
    
    def validate_text_input(self, text: str) -> bool:
        """Validate text input for dangerous patterns"""
        if not text:
            return True
        
        # Check length
        if len(text) > self.max_text_length:
            return False
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if pattern.search(text):
                return False
        
        return True


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(self, app, config: Dict[str, Any] = None):
        super().__init__(app)
        self.config = config or {}
        
        # Rate limiting configuration
        self.requests_per_minute = self.config.get("requests_per_minute", 1000)
        self.requests_per_second = self.config.get("requests_per_second", 100)
        self.window_size = 60  # 1 minute
        
        # In-memory storage (use Redis in production)
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque())
        self.last_cleanup = time.time()
        
        # Exempt endpoints (health checks, etc.)
        self.exempt_paths = self.config.get("exempt_paths", ["/health", "/ready"])
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Cleanup old entries periodically
        current_time = time.time()
        if current_time - self.last_cleanup > 60:  # Cleanup every minute
            self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time
        
        # Check rate limits
        if self._is_rate_limited(client_id, current_time):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limited",
                    "message": "Rate limit exceeded",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Record request
        self.request_counts[client_id].append(current_time)
        
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get API key from request body for more precise limiting
        api_key = getattr(request.state, "api_key", None)
        if api_key:
            return f"api_key:{api_key}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _is_rate_limited(self, client_id: str, current_time: float) -> bool:
        """Check if client is rate limited"""
        requests = self.request_counts[client_id]
        
        # Remove old requests outside the window
        cutoff_time = current_time - self.window_size
        while requests and requests[0] < cutoff_time:
            requests.popleft()
        
        # Check if rate limit exceeded
        return len(requests) >= self.requests_per_minute
    
    def _cleanup_old_entries(self, current_time: float):
        """Clean up old request tracking entries"""
        cutoff_time = current_time - self.window_size * 2  # Keep some buffer
        
        for client_id in list(self.request_counts.keys()):
            requests = self.request_counts[client_id]
            
            # Remove old requests
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            
            # Remove empty entries
            if not requests:
                del self.request_counts[client_id]


class SecurityMiddlewareManager:
    """Manager for security middleware configuration"""
    
    @staticmethod
    def create_middleware_stack(app, config: Dict[str, Any] = None):
        """Create and configure security middleware stack"""
        if not config:
            config = {}
        
        # Add middleware in reverse order (they wrap each other)
        
        # Rate limiting (outermost)
        if config.get("enable_rate_limiting", True):
            app.add_middleware(
                RateLimitingMiddleware,
                config=config.get("rate_limiting", {})
            )
        
        # Input validation
        if config.get("enable_input_validation", True):
            app.add_middleware(
                InputValidationMiddleware,
                config=config.get("input_validation", {})
            )
        
        # Security headers (innermost, closest to response)
        if config.get("enable_security_headers", True):
            app.add_middleware(
                SecurityHeadersMiddleware,
                config=config.get("security_headers", {})
            )
        
        return app
    
    @staticmethod
    def get_security_status(app) -> Dict[str, Any]:
        """Get security middleware status"""
        # Check which middleware are enabled
        middleware_list = []
        for middleware in app.middleware_stack:
            middleware_name = middleware.cls.__name__
            if "Security" in middleware_name or "RateLimit" in middleware_name or "InputValidation" in middleware_name:
                middleware_list.append(middleware_name)
        
        return {
            "enabled_middleware": middleware_list,
            "security_headers_active": "SecurityHeadersMiddleware" in middleware_list,
            "rate_limiting_active": "RateLimitingMiddleware" in middleware_list,
            "input_validation_active": "InputValidationMiddleware" in middleware_list,
        }