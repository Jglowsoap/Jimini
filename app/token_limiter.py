"""
Token-based rate limiting for LLM API calls.

Tracks token consumption per API key with configurable quotas (TPM, hourly, daily).
Pre-calculates prompt tokens to prevent unnecessary LLM calls when quota is exceeded.

Inspired by Azure APIM AI Gateway's token limit policies.
"""
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
import os

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("[TokenLimiter] Warning: tiktoken not available, using character-based estimation")


@dataclass
class TokenQuota:
    """Token quota configuration per API key"""
    tokens_per_minute: int = 10_000
    tokens_per_hour: int = 500_000
    tokens_per_day: int = 10_000_000
    
    
@dataclass
class TokenUsage:
    """Token usage record"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class TokenRateLimiter:
    """
    Rate limiter based on LLM token consumption.
    
    Features:
    - Per-API-key token quotas (TPM, hourly, daily)
    - Pre-calculation of prompt tokens before LLM call
    - Token usage tracking and reporting
    - Integration with OpenAI token counting (tiktoken)
    - Automatic cleanup of old usage records
    
    Usage:
        limiter = TokenRateLimiter()
        limiter.set_quota("api-key-123", TokenQuota(tokens_per_minute=5000))
        
        # Before LLM call
        estimated = limiter.estimate_prompt_tokens("Hello, world!")
        allowed, reason = limiter.check_quota("api-key-123", estimated)
        
        if allowed:
            # Make LLM call...
            limiter.record_usage("api-key-123", prompt_tokens=10, completion_tokens=50)
    """
    
    def __init__(self):
        self.quotas: Dict[str, TokenQuota] = {}
        self.usage: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Initialize tiktoken encoding for GPT-4/4o models
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4, GPT-4o
            except Exception as e:
                print(f"[TokenLimiter] Failed to load tiktoken encoding: {e}")
                self.encoding = None
        else:
            self.encoding = None
            
        # Set default quota
        self.default_quota = TokenQuota()
        
    def set_quota(self, api_key: str, quota: TokenQuota):
        """Set token quota for specific API key"""
        self.quotas[api_key] = quota
        
    def get_quota(self, api_key: str) -> TokenQuota:
        """Get quota for API key (or default)"""
        return self.quotas.get(api_key, self.default_quota)
        
    def estimate_prompt_tokens(self, text: str) -> int:
        """
        Estimate tokens in prompt before sending to LLM.
        
        Uses tiktoken if available, otherwise uses character-based estimation.
        """
        if self.encoding:
            try:
                return len(self.encoding.encode(text))
            except Exception:
                pass
                
        # Fallback: rough estimation (1 token ≈ 4 characters)
        return len(text) // 4
        
    def check_quota(self, api_key: str, estimated_tokens: int) -> Tuple[bool, str]:
        """
        Check if request would exceed quota.
        
        Args:
            api_key: API key identifier
            estimated_tokens: Estimated tokens for this request
            
        Returns:
            (allowed: bool, reason: str)
        """
        quota = self.get_quota(api_key)
        usage_window = self.usage[api_key]
        now = datetime.now()
        
        # Calculate current usage in different windows
        minute_tokens = self._count_tokens_in_window(usage_window, now, timedelta(minutes=1))
        hour_tokens = self._count_tokens_in_window(usage_window, now, timedelta(hours=1))
        day_tokens = self._count_tokens_in_window(usage_window, now, timedelta(days=1))
        
        # Check against quotas (including estimated tokens for this request)
        if minute_tokens + estimated_tokens > quota.tokens_per_minute:
            return False, f"TPM quota exceeded: {minute_tokens + estimated_tokens}/{quota.tokens_per_minute} (would use {estimated_tokens} more)"
            
        if hour_tokens + estimated_tokens > quota.tokens_per_hour:
            return False, f"Hourly quota exceeded: {hour_tokens + estimated_tokens}/{quota.tokens_per_hour} (would use {estimated_tokens} more)"
            
        if day_tokens + estimated_tokens > quota.tokens_per_day:
            return False, f"Daily quota exceeded: {day_tokens + estimated_tokens}/{quota.tokens_per_day} (would use {estimated_tokens} more)"
            
        return True, "OK"
        
    def record_usage(self, api_key: str, prompt_tokens: int, completion_tokens: int):
        """
        Record actual token usage after LLM call.
        
        Args:
            api_key: API key identifier
            prompt_tokens: Tokens used in prompt
            completion_tokens: Tokens used in completion
        """
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            timestamp=datetime.now()
        )
        self.usage[api_key].append(usage)
        
        # Clean old entries periodically (keep last 24 hours)
        self._cleanup_old_usage(api_key)
        
    def get_usage_stats(self, api_key: str) -> Dict[str, Any]:
        """
        Get usage statistics for API key.
        
        Returns:
            Dictionary with current usage and quota information
        """
        usage_window = self.usage[api_key]
        now = datetime.now()
        quota = self.get_quota(api_key)
        
        minute_tokens = self._count_tokens_in_window(usage_window, now, timedelta(minutes=1))
        hour_tokens = self._count_tokens_in_window(usage_window, now, timedelta(hours=1))
        day_tokens = self._count_tokens_in_window(usage_window, now, timedelta(days=1))
        
        return {
            "api_key": api_key,
            "current_usage": {
                "tokens_last_minute": minute_tokens,
                "tokens_last_hour": hour_tokens,
                "tokens_last_day": day_tokens
            },
            "quota": {
                "tokens_per_minute": quota.tokens_per_minute,
                "tokens_per_hour": quota.tokens_per_hour,
                "tokens_per_day": quota.tokens_per_day
            },
            "remaining": {
                "minute": max(0, quota.tokens_per_minute - minute_tokens),
                "hour": max(0, quota.tokens_per_hour - hour_tokens),
                "day": max(0, quota.tokens_per_day - day_tokens)
            },
            "utilization": {
                "minute_pct": (minute_tokens / quota.tokens_per_minute * 100) if quota.tokens_per_minute > 0 else 0,
                "hour_pct": (hour_tokens / quota.tokens_per_hour * 100) if quota.tokens_per_hour > 0 else 0,
                "day_pct": (day_tokens / quota.tokens_per_day * 100) if quota.tokens_per_day > 0 else 0
            },
            "total_requests": len(usage_window),
            "encoding": "tiktoken (cl100k_base)" if self.encoding else "character-based estimation"
        }
        
    def get_all_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all API keys"""
        return {
            api_key: self.get_usage_stats(api_key)
            for api_key in self.usage.keys()
        }
        
    def _count_tokens_in_window(self, usage_window: deque, now: datetime, window: timedelta) -> int:
        """Count tokens used within time window"""
        cutoff = now - window
        return sum(u.total_tokens for u in usage_window if u.timestamp >= cutoff)
        
    def _cleanup_old_usage(self, api_key: str):
        """Remove usage records older than 24 hours"""
        cutoff = datetime.now() - timedelta(days=1)
        usage_window = self.usage[api_key]
        
        # Remove old records from the left (oldest)
        while usage_window and usage_window[0].timestamp < cutoff:
            usage_window.popleft()


# Global instance
token_limiter = TokenRateLimiter()


def load_token_quotas_from_config(config: Dict[str, Any]):
    """
    Load token quotas from configuration.
    
    Expected config format:
        token_quotas:
          default:
            tokens_per_minute: 10000
            tokens_per_hour: 500000
            tokens_per_day: 10000000
          tiers:
            premium:
              tokens_per_minute: 50000
              tokens_per_hour: 2000000
              tokens_per_day: 50000000
          api_keys:
            "api-key-123": "premium"
            "api-key-456": "default"
    """
    if "token_quotas" not in config:
        return
        
    quotas_config = config["token_quotas"]
    
    # Set default quota
    if "default" in quotas_config:
        default = quotas_config["default"]
        token_limiter.default_quota = TokenQuota(
            tokens_per_minute=default.get("tokens_per_minute", 10_000),
            tokens_per_hour=default.get("tokens_per_hour", 500_000),
            tokens_per_day=default.get("tokens_per_day", 10_000_000)
        )
    
    # Load tier definitions
    tiers = {}
    if "tiers" in quotas_config:
        for tier_name, tier_config in quotas_config["tiers"].items():
            tiers[tier_name] = TokenQuota(
                tokens_per_minute=tier_config.get("tokens_per_minute", 10_000),
                tokens_per_hour=tier_config.get("tokens_per_hour", 500_000),
                tokens_per_day=tier_config.get("tokens_per_day", 10_000_000)
            )
    
    # Assign quotas to API keys
    if "api_keys" in quotas_config:
        for api_key, tier_name in quotas_config["api_keys"].items():
            if tier_name in tiers:
                token_limiter.set_quota(api_key, tiers[tier_name])
            elif tier_name == "default":
                token_limiter.set_quota(api_key, token_limiter.default_quota)
