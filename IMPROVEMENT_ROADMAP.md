# 🚀 Jimini Improvement Roadmap - Learning from Azure APIM & Competitors

**Based on Competitive Analysis of Azure API Management, Kong, AWS API Gateway**  
**Date**: November 5, 2025

---

## Executive Summary

This document outlines **concrete, implementable improvements** for Jimini inspired by Azure APIM AI Gateway and other enterprise platforms. Focus is on features that **enhance Jimini's core value** (security & compliance) while addressing competitive gaps.

### Priority Framework

**🔴 Critical**: Features blocking enterprise adoption  
**🟡 Important**: Features improving competitive position  
**🟢 Nice-to-Have**: Features for future differentiation

---

## 1. Token-Based Rate Limiting (🔴 Critical)

### Problem
Azure APIM has sophisticated **tokens-per-minute (TPM)** quotas for LLM usage. Jimini only has basic request rate limiting, which doesn't account for LLM-specific economics.

### Solution: LLM Token Quota Management

#### Implementation Plan

**File**: `app/token_limiter.py`

```python
"""
Token-based rate limiting for LLM API calls.
Tracks token consumption per API key with configurable quotas.
"""
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional
import tiktoken  # OpenAI's token counting library

@dataclass
class TokenQuota:
    """Token quota configuration per API key"""
    tokens_per_minute: int = 10_000
    tokens_per_hour: int = 500_000
    tokens_per_day: int = 10_000_000
    
@dataclass
class TokenUsage:
    """Token usage tracking"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    timestamp: datetime = None

class TokenRateLimiter:
    """
    Rate limiter based on LLM token consumption.
    
    Features:
    - Per-API-key token quotas (TPM, hourly, daily)
    - Pre-calculation of prompt tokens before LLM call
    - Token usage tracking and reporting
    - Integration with OpenAI token counting
    """
    
    def __init__(self):
        self.quotas: Dict[str, TokenQuota] = {}
        self.usage: Dict[str, deque] = defaultdict(lambda: deque())
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        
    def set_quota(self, api_key: str, quota: TokenQuota):
        """Set token quota for API key"""
        self.quotas[api_key] = quota
        
    def estimate_prompt_tokens(self, text: str) -> int:
        """Estimate tokens in prompt before sending to LLM"""
        return len(self.encoding.encode(text))
        
    def check_quota(self, api_key: str, estimated_tokens: int) -> tuple[bool, str]:
        """
        Check if request would exceed quota.
        
        Returns:
            (allowed: bool, reason: str)
        """
        quota = self.quotas.get(api_key, TokenQuota())
        usage_window = self.usage[api_key]
        now = datetime.now()
        
        # Calculate current usage in different windows
        minute_tokens = self._count_tokens_in_window(usage_window, now, timedelta(minutes=1))
        hour_tokens = self._count_tokens_in_window(usage_window, now, timedelta(hours=1))
        day_tokens = self._count_tokens_in_window(usage_window, now, timedelta(days=1))
        
        # Check against quotas (including estimated tokens for this request)
        if minute_tokens + estimated_tokens > quota.tokens_per_minute:
            return False, f"TPM quota exceeded: {minute_tokens}/{quota.tokens_per_minute}"
        if hour_tokens + estimated_tokens > quota.tokens_per_hour:
            return False, f"Hourly quota exceeded: {hour_tokens}/{quota.tokens_per_hour}"
        if day_tokens + estimated_tokens > quota.tokens_per_day:
            return False, f"Daily quota exceeded: {day_tokens}/{quota.tokens_per_day}"
            
        return True, "OK"
        
    def record_usage(self, api_key: str, prompt_tokens: int, completion_tokens: int):
        """Record actual token usage after LLM call"""
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            timestamp=datetime.now()
        )
        self.usage[api_key].append(usage)
        
        # Clean old entries (older than 1 day)
        self._cleanup_old_usage(api_key)
        
    def get_usage_stats(self, api_key: str) -> Dict:
        """Get usage statistics for API key"""
        usage_window = self.usage[api_key]
        now = datetime.now()
        
        return {
            "tokens_last_minute": self._count_tokens_in_window(usage_window, now, timedelta(minutes=1)),
            "tokens_last_hour": self._count_tokens_in_window(usage_window, now, timedelta(hours=1)),
            "tokens_last_day": self._count_tokens_in_window(usage_window, now, timedelta(days=1)),
            "quota": {
                "tpm": self.quotas.get(api_key, TokenQuota()).tokens_per_minute,
                "hourly": self.quotas.get(api_key, TokenQuota()).tokens_per_hour,
                "daily": self.quotas.get(api_key, TokenQuota()).tokens_per_day,
            }
        }
        
    def _count_tokens_in_window(self, usage_window: deque, now: datetime, window: timedelta) -> int:
        """Count tokens used within time window"""
        cutoff = now - window
        return sum(u.total_tokens for u in usage_window if u.timestamp >= cutoff)
        
    def _cleanup_old_usage(self, api_key: str):
        """Remove usage records older than 1 day"""
        cutoff = datetime.now() - timedelta(days=1)
        usage_window = self.usage[api_key]
        while usage_window and usage_window[0].timestamp < cutoff:
            usage_window.popleft()

# Global instance
token_limiter = TokenRateLimiter()
```

#### Integration with Evaluation Endpoint

**File**: `app/main.py` (add to `/v1/evaluate` endpoint)

```python
from app.token_limiter import token_limiter, TokenQuota

# Before LLM call in evaluate endpoint
if llm_rule_triggered:
    # Estimate tokens in prompt
    estimated_tokens = token_limiter.estimate_prompt_tokens(request.text)
    
    # Check quota
    allowed, reason = token_limiter.check_quota(api_key, estimated_tokens)
    if not allowed:
        return EvaluateResponse(
            action="block",
            rule_ids=["TOKEN-QUOTA-EXCEEDED"],
            message=reason,
            metadata={"quota_exceeded": True}
        )
    
    # Make LLM call...
    # After LLM call, record actual usage
    token_limiter.record_usage(
        api_key,
        prompt_tokens=llm_response.usage.prompt_tokens,
        completion_tokens=llm_response.usage.completion_tokens
    )
```

#### Configuration

**File**: `policy_rules.yaml` (add quota config)

```yaml
token_quotas:
  default:
    tokens_per_minute: 10000
    tokens_per_hour: 500000
    tokens_per_day: 10000000
    
  premium:
    tokens_per_minute: 50000
    tokens_per_hour: 2000000
    tokens_per_day: 50000000
    
  api_keys:
    "gov-agency-key": "premium"
    "test-key": "default"
```

#### New API Endpoint

```python
@app.get("/v1/token-usage/{api_key}")
async def get_token_usage(api_key: str):
    """Get token usage statistics for API key"""
    return token_limiter.get_usage_stats(api_key)
```

**Benefit**: Prevents runaway LLM costs, enables fair resource allocation across teams.

**Effort**: 2-3 days  
**Impact**: HIGH - Critical for enterprise LLM deployments

---

## 2. Semantic Caching (🟡 Important)

### Problem
Azure APIM uses Redis + embeddings to cache semantically similar LLM responses. This drastically reduces costs and latency for repeated queries.

### Solution: Vector-Based Response Cache

#### Implementation Plan

**File**: `app/semantic_cache.py`

```python
"""
Semantic caching for LLM responses using vector similarity.
Caches responses and retrieves them for semantically similar prompts.
"""
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import numpy as np

try:
    import redis
    from sentence_transformers import SentenceTransformer
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

class SemanticCache:
    """
    Semantic cache for LLM responses.
    
    Features:
    - Vector embeddings for prompt similarity
    - Configurable similarity threshold
    - TTL for cache entries
    - Redis backend for distributed caching
    """
    
    def __init__(
        self, 
        redis_url: str = "redis://localhost:6379",
        similarity_threshold: float = 0.95,
        ttl_seconds: int = 3600
    ):
        if not CACHE_AVAILABLE:
            raise RuntimeError("Redis and sentence-transformers required for semantic caching")
            
        self.redis_client = redis.from_url(redis_url)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight, fast
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        
    def get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text"""
        return self.model.encode(text)
        
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between vectors"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
    def lookup(self, prompt: str, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Look up cached response for semantically similar prompt.
        
        Returns cached response if similarity > threshold, else None.
        """
        # Generate embedding for incoming prompt
        prompt_embedding = self.get_embedding(prompt)
        
        # Search cache for similar prompts (scan by rule_id)
        cache_key_pattern = f"semantic_cache:{rule_id}:*"
        
        for cache_key in self.redis_client.scan_iter(match=cache_key_pattern):
            cached_data = self.redis_client.get(cache_key)
            if not cached_data:
                continue
                
            cached = json.loads(cached_data)
            cached_embedding = np.array(cached["embedding"])
            
            # Calculate similarity
            similarity = self.cosine_similarity(prompt_embedding, cached_embedding)
            
            if similarity >= self.similarity_threshold:
                # Cache hit!
                return {
                    "response": cached["response"],
                    "similarity": float(similarity),
                    "cached_at": cached["timestamp"],
                    "cache_hit": True
                }
                
        return None  # Cache miss
        
    def store(self, prompt: str, rule_id: str, response: str):
        """Store LLM response in cache with embedding"""
        prompt_embedding = self.get_embedding(prompt)
        
        # Create cache key (hash of prompt for uniqueness)
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        cache_key = f"semantic_cache:{rule_id}:{prompt_hash}"
        
        # Store with TTL
        cache_data = {
            "prompt": prompt,
            "embedding": prompt_embedding.tolist(),
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        self.redis_client.setex(
            cache_key,
            self.ttl_seconds,
            json.dumps(cache_data)
        )
        
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_entries = len(list(self.redis_client.scan_iter(match="semantic_cache:*")))
        
        return {
            "total_cached_prompts": total_entries,
            "similarity_threshold": self.similarity_threshold,
            "ttl_seconds": self.ttl_seconds,
            "cache_backend": "redis"
        }

# Global instance (lazy init)
_semantic_cache: Optional[SemanticCache] = None

def get_semantic_cache() -> Optional[SemanticCache]:
    """Get or initialize semantic cache"""
    global _semantic_cache
    if _semantic_cache is None:
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            _semantic_cache = SemanticCache(redis_url=redis_url)
        except Exception as e:
            print(f"Semantic cache not available: {e}")
            return None
    return _semantic_cache
```

#### Integration with LLM Checks

**File**: `app/enforcement.py` (modify `llm_policy_check`)

```python
from app.semantic_cache import get_semantic_cache

def llm_policy_check(text: str, prompt: str, rule_id: str, model: str = "gpt-4o-mini") -> bool:
    """
    LLM policy check with semantic caching.
    """
    # Check semantic cache first
    cache = get_semantic_cache()
    if cache:
        cached_response = cache.lookup(text, rule_id)
        if cached_response:
            # Cache hit - return cached result
            answer = cached_response["response"].strip().lower()
            print(f"[Cache Hit] Similarity: {cached_response['similarity']:.3f}")
            return answer.startswith("yes")
    
    # Cache miss - call LLM
    _ensure_openai()
    if _openai_client is False:
        return False
        
    try:
        resp = _openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            max_tokens=50,
            temperature=0,
        )
        content = resp.choices[0].message.content or ""
        answer = content.strip().lower()
        
        # Store in cache for future use
        if cache:
            cache.store(text, rule_id, answer)
            
        return answer.startswith("yes")
    except Exception:
        return False
```

#### Configuration

**File**: `jimini.config.yaml`

```yaml
semantic_cache:
  enabled: true
  redis_url: "redis://localhost:6379"
  similarity_threshold: 0.95  # 95% similarity required
  ttl_seconds: 3600  # 1 hour cache
```

#### Metrics

Add to `/v1/metrics`:

```python
{
  "semantic_cache": {
    "total_lookups": 1000,
    "cache_hits": 750,
    "cache_misses": 250,
    "hit_rate": 0.75,
    "avg_similarity": 0.97,
    "cost_savings_usd": 15.50  # Estimated based on avoided LLM calls
  }
}
```

**Benefit**: 50-80% reduction in LLM costs, <50ms responses for cached queries.

**Effort**: 3-4 days (including Redis setup, testing)  
**Impact**: HIGH - Major cost/performance improvement

---

## 3. Backend Load Balancing (🟡 Important)

### Problem
Azure APIM can distribute requests across multiple LLM endpoints with round-robin, weighted, or priority strategies. Jimini currently supports one LLM endpoint.

### Solution: Multi-Backend LLM Router

#### Implementation Plan

**File**: `app/llm_backends.py`

```python
"""
Load balancing across multiple LLM backends.
Supports round-robin, weighted, and priority-based routing.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
import random
from collections import deque

class LoadBalanceStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    PRIORITY = "priority"
    LEAST_LOADED = "least_loaded"

@dataclass
class LLMBackend:
    """LLM backend configuration"""
    name: str
    api_key: str
    endpoint: str  # e.g., "openai", "azure", "anthropic"
    model: str
    priority: int = 1  # Higher = higher priority
    weight: int = 1  # For weighted distribution
    max_tpm: int = 10000  # Max tokens per minute
    current_load: int = 0  # Current tokens in use
    health_status: str = "healthy"  # healthy, degraded, unhealthy
    
class LLMLoadBalancer:
    """
    Load balancer for multiple LLM backends.
    
    Features:
    - Multiple routing strategies
    - Health checking
    - Automatic failover
    - Load tracking
    """
    
    def __init__(self, strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN):
        self.backends: List[LLMBackend] = []
        self.strategy = strategy
        self.current_index = 0
        
    def add_backend(self, backend: LLMBackend):
        """Add LLM backend to pool"""
        self.backends.append(backend)
        
    def get_next_backend(self, estimated_tokens: int = 0) -> Optional[LLMBackend]:
        """
        Select next backend based on strategy.
        
        Returns None if no healthy backends available.
        """
        healthy_backends = [b for b in self.backends if b.health_status == "healthy"]
        
        if not healthy_backends:
            # Try degraded backends as fallback
            healthy_backends = [b for b in self.backends if b.health_status == "degraded"]
            
        if not healthy_backends:
            return None
            
        if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin(healthy_backends)
        elif self.strategy == LoadBalanceStrategy.WEIGHTED:
            return self._weighted(healthy_backends)
        elif self.strategy == LoadBalanceStrategy.PRIORITY:
            return self._priority(healthy_backends, estimated_tokens)
        elif self.strategy == LoadBalanceStrategy.LEAST_LOADED:
            return self._least_loaded(healthy_backends, estimated_tokens)
        else:
            return healthy_backends[0]
            
    def _round_robin(self, backends: List[LLMBackend]) -> LLMBackend:
        """Round-robin selection"""
        backend = backends[self.current_index % len(backends)]
        self.current_index += 1
        return backend
        
    def _weighted(self, backends: List[LLMBackend]) -> LLMBackend:
        """Weighted random selection"""
        weights = [b.weight for b in backends]
        return random.choices(backends, weights=weights)[0]
        
    def _priority(self, backends: List[LLMBackend], estimated_tokens: int) -> LLMBackend:
        """
        Priority-based selection.
        Use highest priority backend that has capacity.
        """
        sorted_backends = sorted(backends, key=lambda b: b.priority, reverse=True)
        
        for backend in sorted_backends:
            if backend.current_load + estimated_tokens <= backend.max_tpm:
                return backend
                
        # If all full, return highest priority anyway
        return sorted_backends[0]
        
    def _least_loaded(self, backends: List[LLMBackend], estimated_tokens: int) -> LLMBackend:
        """Select backend with least current load"""
        return min(backends, key=lambda b: b.current_load)
        
    def record_usage(self, backend_name: str, tokens: int):
        """Record token usage for backend"""
        for backend in self.backends:
            if backend.name == backend_name:
                backend.current_load += tokens
                break
                
    def reset_load(self):
        """Reset load counters (call every minute)"""
        for backend in self.backends:
            backend.current_load = 0
            
    def mark_unhealthy(self, backend_name: str):
        """Mark backend as unhealthy"""
        for backend in self.backends:
            if backend.name == backend_name:
                backend.health_status = "unhealthy"
                break
                
    def mark_healthy(self, backend_name: str):
        """Mark backend as healthy"""
        for backend in self.backends:
            if backend.name == backend_name:
                backend.health_status = "healthy"
                break
                
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        return {
            "strategy": self.strategy.value,
            "total_backends": len(self.backends),
            "healthy_backends": sum(1 for b in self.backends if b.health_status == "healthy"),
            "backends": [
                {
                    "name": b.name,
                    "health": b.health_status,
                    "current_load": b.current_load,
                    "capacity": b.max_tpm,
                    "utilization": f"{(b.current_load / b.max_tpm * 100):.1f}%"
                }
                for b in self.backends
            ]
        }

# Global instance
llm_load_balancer = LLMLoadBalancer()
```

#### Configuration

**File**: `policy_rules.yaml`

```yaml
llm_backends:
  strategy: "priority"  # round_robin, weighted, priority, least_loaded
  
  backends:
    - name: "azure-openai-east"
      endpoint: "azure"
      api_key: "${AZURE_OPENAI_KEY_EAST}"
      model: "gpt-4o"
      priority: 1  # Highest priority (PTU instance)
      max_tpm: 50000
      
    - name: "azure-openai-west"
      endpoint: "azure"
      api_key: "${AZURE_OPENAI_KEY_WEST}"
      model: "gpt-4o"
      priority: 1
      max_tpm: 50000
      
    - name: "openai-fallback"
      endpoint: "openai"
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4o-mini"
      priority: 2  # Fallback (pay-as-you-go)
      max_tpm: 10000
```

#### Integration

**File**: `app/enforcement.py`

```python
from app.llm_backends import llm_load_balancer

def llm_policy_check(text: str, prompt: str, model: str = "gpt-4o-mini") -> bool:
    # Get next available backend
    estimated_tokens = len(text) // 4  # Rough estimate
    backend = llm_load_balancer.get_next_backend(estimated_tokens)
    
    if not backend:
        print("[LLM] No healthy backends available")
        return False
        
    try:
        # Call LLM using selected backend
        if backend.endpoint == "azure":
            # Use Azure OpenAI client
            response = call_azure_openai(backend, text, prompt)
        else:
            # Use standard OpenAI client
            response = call_openai(backend, text, prompt)
            
        # Record usage
        llm_load_balancer.record_usage(backend.name, response.usage.total_tokens)
        
        return response.choices[0].message.content.lower().startswith("yes")
        
    except Exception as e:
        # Mark backend unhealthy on failure
        llm_load_balancer.mark_unhealthy(backend.name)
        print(f"[LLM] Backend {backend.name} failed: {e}")
        return False
```

**Benefit**: Maximize PTU utilization, automatic failover, avoid rate limits.

**Effort**: 4-5 days  
**Impact**: MEDIUM - Important for enterprise deployments with multiple LLM endpoints

---

## 4. Enhanced Observability Dashboard (🟢 Nice-to-Have)

### Problem
Azure APIM has built-in analytics dashboards in the portal. Jimini has CLI metrics but no visual dashboard.

### Solution: Real-Time Web Dashboard

#### Implementation Plan

**File**: `app/dashboard.py` (new FastAPI HTML endpoint)

```python
"""
Real-time observability dashboard for Jimini.
"""
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

@app.get("/dashboard", response_class=HTMLResponse)
async def observability_dashboard(request: Request):
    """Real-time observability dashboard"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Jimini Observability Dashboard"
    })

@app.get("/api/dashboard/metrics")
async def dashboard_metrics():
    """API endpoint for dashboard data"""
    return {
        "timestamp": datetime.now().isoformat(),
        "requests": {
            "total": metrics_collector.total_requests,
            "rate_per_minute": calculate_request_rate(),
            "by_decision": {
                "allow": metrics_collector.decisions["allow"],
                "flag": metrics_collector.decisions["flag"],
                "block": metrics_collector.decisions["block"]
            }
        },
        "rules": {
            "total_loaded": len(rules_store.get("rules", [])),
            "top_triggered": get_top_triggered_rules(limit=10)
        },
        "performance": {
            "avg_response_time_ms": calculate_avg_response_time(),
            "p50_ms": calculate_percentile(50),
            "p95_ms": calculate_percentile(95),
            "p99_ms": calculate_percentile(99)
        },
        "llm": {
            "calls": llm_metrics.total_calls,
            "cache_hit_rate": calculate_cache_hit_rate(),
            "avg_tokens": llm_metrics.avg_tokens,
            "cost_usd": llm_metrics.total_cost
        },
        "health": {
            "status": "healthy",
            "uptime_seconds": get_uptime(),
            "circuit_breakers": get_circuit_breaker_states()
        }
    }
```

**File**: `app/templates/dashboard.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Jimini Observability Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto p-6">
        <h1 class="text-3xl font-bold mb-6">🔒 Jimini Observability Dashboard</h1>
        
        <!-- KPI Cards -->
        <div class="grid grid-cols-4 gap-4 mb-6">
            <div class="bg-white p-4 rounded shadow">
                <h3 class="text-gray-600 text-sm">Requests/min</h3>
                <p id="requests-rate" class="text-3xl font-bold">-</p>
            </div>
            <div class="bg-white p-4 rounded shadow">
                <h3 class="text-gray-600 text-sm">Avg Response Time</h3>
                <p id="avg-response" class="text-3xl font-bold">-</p>
            </div>
            <div class="bg-white p-4 rounded shadow">
                <h3 class="text-gray-600 text-sm">Cache Hit Rate</h3>
                <p id="cache-rate" class="text-3xl font-bold">-</p>
            </div>
            <div class="bg-white p-4 rounded shadow">
                <h3 class="text-gray-600 text-sm">LLM Cost (Today)</h3>
                <p id="llm-cost" class="text-3xl font-bold">-</p>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="grid grid-cols-2 gap-4 mb-6">
            <div class="bg-white p-4 rounded shadow">
                <h3 class="font-bold mb-4">Decision Distribution</h3>
                <canvas id="decision-chart"></canvas>
            </div>
            <div class="bg-white p-4 rounded shadow">
                <h3 class="font-bold mb-4">Response Time (P95)</h3>
                <canvas id="latency-chart"></canvas>
            </div>
        </div>
        
        <!-- Top Triggered Rules -->
        <div class="bg-white p-4 rounded shadow">
            <h3 class="font-bold mb-4">Top Triggered Rules</h3>
            <table id="rules-table" class="w-full">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-4 py-2 text-left">Rule ID</th>
                        <th class="px-4 py-2 text-left">Title</th>
                        <th class="px-4 py-2 text-right">Triggers</th>
                    </tr>
                </thead>
                <tbody id="rules-body"></tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 5 seconds
        setInterval(updateDashboard, 5000);
        updateDashboard();
        
        async function updateDashboard() {
            const response = await fetch('/api/dashboard/metrics');
            const data = await response.json();
            
            // Update KPIs
            document.getElementById('requests-rate').textContent = 
                data.requests.rate_per_minute.toFixed(0);
            document.getElementById('avg-response').textContent = 
                data.performance.avg_response_time_ms.toFixed(0) + ' ms';
            document.getElementById('cache-rate').textContent = 
                (data.llm.cache_hit_rate * 100).toFixed(1) + '%';
            document.getElementById('llm-cost').textContent = 
                '$' + data.llm.cost_usd.toFixed(2);
            
            // Update charts...
            updateDecisionChart(data.requests.by_decision);
            updateLatencyChart(data.performance);
            
            // Update rules table...
            updateRulesTable(data.rules.top_triggered);
        }
        
        function updateDecisionChart(decisions) {
            // Chart.js implementation...
        }
    </script>
</body>
</html>
```

**Benefit**: Real-time visibility, executive reporting, operational insights.

**Effort**: 3-4 days  
**Impact**: MEDIUM - Nice for demos and operations teams

---

## 5. Policy Testing Framework (🔴 Critical)

### Problem
Azure APIM has comprehensive testing tools. Jimini has basic CLI testing but no regression testing, policy validation, or CI/CD integration.

### Solution: Automated Policy Testing Suite

#### Implementation Plan

**File**: `tests/test_policies.py`

```python
"""
Automated policy testing framework.
Validates rules against test cases before deployment.
"""
import pytest
from typing import List, Dict
from app.enforcement import evaluate
from app.rules_loader import load_rules
import yaml

class PolicyTestCase:
    """Test case for policy rule"""
    def __init__(
        self,
        name: str,
        text: str,
        expected_action: str,
        expected_rules: List[str],
        endpoint: str = None,
        direction: str = "outbound"
    ):
        self.name = name
        self.text = text
        self.expected_action = expected_action
        self.expected_rules = expected_rules
        self.endpoint = endpoint
        self.direction = direction

def load_test_cases(test_file: str) -> List[PolicyTestCase]:
    """Load test cases from YAML file"""
    with open(test_file) as f:
        data = yaml.safe_load(f)
        
    test_cases = []
    for tc in data.get("test_cases", []):
        test_cases.append(PolicyTestCase(
            name=tc["name"],
            text=tc["text"],
            expected_action=tc["expected_action"],
            expected_rules=tc.get("expected_rules", []),
            endpoint=tc.get("endpoint"),
            direction=tc.get("direction", "outbound")
        ))
    return test_cases

@pytest.mark.parametrize("test_case", load_test_cases("tests/policy_test_cases.yaml"))
def test_policy_rule(test_case: PolicyTestCase):
    """Test individual policy rule"""
    # Load rules
    load_rules("policy_rules.yaml")
    
    # Evaluate
    result = evaluate(
        text=test_case.text,
        endpoint=test_case.endpoint,
        direction=test_case.direction
    )
    
    # Assert action
    assert result["action"] == test_case.expected_action, \
        f"Expected {test_case.expected_action}, got {result['action']}"
    
    # Assert triggered rules
    for expected_rule in test_case.expected_rules:
        assert expected_rule in result["rule_ids"], \
            f"Expected rule {expected_rule} not triggered"

def test_no_false_positives():
    """Ensure legitimate content is not blocked"""
    legitimate_texts = [
        "The meeting is scheduled for 3pm tomorrow.",
        "Our product roadmap includes three new features.",
        "Please review the attached document and provide feedback.",
    ]
    
    load_rules("policy_rules.yaml")
    
    for text in legitimate_texts:
        result = evaluate(text=text)
        assert result["action"] in ["allow", "flag"], \
            f"False positive: legitimate text blocked: {text}"

def test_rule_coverage():
    """Ensure all rules have test cases"""
    load_rules("policy_rules.yaml")
    test_cases = load_test_cases("tests/policy_test_cases.yaml")
    
    # Get all rule IDs
    from app.rules_loader import rules_store
    all_rule_ids = {rule["id"] for rule in rules_store.get("rules", [])}
    
    # Get tested rule IDs
    tested_rule_ids = set()
    for tc in test_cases:
        tested_rule_ids.update(tc.expected_rules)
    
    # Find untested rules
    untested = all_rule_ids - tested_rule_ids
    
    assert len(untested) == 0, \
        f"Untested rules: {untested}"
```

**File**: `tests/policy_test_cases.yaml`

```yaml
# Policy test cases for automated validation
test_cases:
  # PII Detection
  - name: "SSN Detection"
    text: "Patient SSN: 123-45-6789"
    expected_action: "block"
    expected_rules: ["SSN-1.0"]
    
  - name: "Email Detection"
    text: "Contact me at user@example.com for more info"
    expected_action: "flag"
    expected_rules: ["EMAIL-1.0"]
    
  # Secret Detection
  - name: "GitHub Token"
    text: "Use this token: ghp_1234567890abcdefghijklmnopqrstuvwx"
    expected_action: "block"
    expected_rules: ["GITHUB-TOKEN-1.0"]
    
  - name: "OpenAI API Key"
    text: "sk-proj-1234567890abcdefghijklmnopqrstuvwxyz"
    expected_action: "block"
    expected_rules: ["OPENAI-KEY-1.0"]
    
  # Legitimate Content (No False Positives)
  - name: "Normal Business Email"
    text: "The quarterly meeting is scheduled for next week."
    expected_action: "allow"
    expected_rules: []
    
  - name: "Technical Discussion"
    text: "We should implement OAuth 2.0 authentication."
    expected_action: "allow"
    expected_rules: []
```

#### CI/CD Integration

**File**: `.github/workflows/policy-tests.yml`

```yaml
name: Policy Tests

on:
  pull_request:
    paths:
      - 'policy_rules.yaml'
      - 'packs/**/*.yaml'
      - 'tests/policy_test_cases.yaml'

jobs:
  test-policies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
          
      - name: Lint policies
        run: jimini lint --rules policy_rules.yaml
        
      - name: Run policy tests
        run: pytest tests/test_policies.py -v
        
      - name: Check rule coverage
        run: pytest tests/test_policies.py::test_rule_coverage
        
      - name: Report results
        if: failure()
        run: echo "Policy tests failed! Review changes before merging."
```

**Benefit**: Prevents policy regressions, enables safe rule updates, builds confidence.

**Effort**: 2-3 days  
**Impact**: HIGH - Critical for production deployments

---

## 6. Multi-Tenancy Support (🟡 Important)

### Problem
Azure APIM supports multi-tenant deployments with per-tenant quotas, policies, and isolation. Jimini is single-tenant.

### Solution: Tenant-Aware Policy Engine

#### Implementation Plan

**File**: `app/models.py` (add tenant field)

```python
class EvaluateRequest(BaseModel):
    text: str
    api_key: str
    endpoint: Optional[str] = None
    direction: str = "outbound"
    tenant_id: Optional[str] = None  # NEW: Tenant identifier
    metadata: Optional[Dict[str, Any]] = None
```

**File**: `app/tenants.py`

```python
"""
Multi-tenancy support for Jimini.
Enables tenant-specific policies, quotas, and isolation.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import yaml

@dataclass
class TenantConfig:
    """Tenant-specific configuration"""
    tenant_id: str
    name: str
    rules_pack: str  # Path to tenant-specific rules
    token_quota: Dict[str, int]
    features: Dict[str, bool]
    metadata: Dict[str, Any]

class TenantManager:
    """Manages multi-tenant configurations"""
    
    def __init__(self):
        self.tenants: Dict[str, TenantConfig] = {}
        
    def load_tenants(self, config_file: str):
        """Load tenant configurations"""
        with open(config_file) as f:
            data = yaml.safe_load(f)
            
        for tenant_data in data.get("tenants", []):
            tenant = TenantConfig(
                tenant_id=tenant_data["tenant_id"],
                name=tenant_data["name"],
                rules_pack=tenant_data.get("rules_pack", "policy_rules.yaml"),
                token_quota=tenant_data.get("token_quota", {}),
                features=tenant_data.get("features", {}),
                metadata=tenant_data.get("metadata", {})
            )
            self.tenants[tenant.tenant_id] = tenant
            
    def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant configuration"""
        return self.tenants.get(tenant_id)
        
    def get_tenant_rules(self, tenant_id: str) -> str:
        """Get rules pack for tenant"""
        tenant = self.get_tenant(tenant_id)
        return tenant.rules_pack if tenant else "policy_rules.yaml"

# Global instance
tenant_manager = TenantManager()
```

**File**: `tenants.yaml`

```yaml
tenants:
  - tenant_id: "healthcare-org"
    name: "Healthcare Organization"
    rules_pack: "packs/hipaa/v1.yaml"
    token_quota:
      tpm: 50000
      daily: 10000000
    features:
      llm_checks: true
      semantic_cache: true
      pii_redaction: true
      
  - tenant_id: "fintech-corp"
    name: "Financial Services Corp"
    rules_pack: "packs/pci/v1.yaml"
    token_quota:
      tpm: 100000
      daily: 50000000
    features:
      llm_checks: true
      semantic_cache: true
      
  - tenant_id: "gov-agency"
    name: "Government Agency"
    rules_pack: "packs/cjis/v1.yaml"
    token_quota:
      tpm: 20000
      daily: 5000000
    features:
      llm_checks: false  # Disable external LLM calls
      audit_chain: true
```

#### Integration

**File**: `app/main.py`

```python
from app.tenants import tenant_manager

@app.on_event("startup")
async def load_tenant_configs():
    tenant_manager.load_tenants("tenants.yaml")

@app.post("/v1/evaluate")
async def evaluate_policy(request: EvaluateRequest) -> EvaluateResponse:
    # Get tenant-specific rules
    if request.tenant_id:
        rules_pack = tenant_manager.get_tenant_rules(request.tenant_id)
        load_rules(rules_pack)
    
    # Evaluate with tenant context...
    result = evaluate(
        text=request.text,
        endpoint=request.endpoint,
        direction=request.direction,
        tenant_id=request.tenant_id
    )
    
    return EvaluateResponse(**result)
```

**Benefit**: SaaS deployments, per-customer isolation, flexible pricing tiers.

**Effort**: 3-4 days  
**Impact**: MEDIUM - Enables SaaS business model

---

## Implementation Priority

### Phase 1: Foundation (Weeks 1-2)
1. ✅ **Token Rate Limiting** - Critical for LLM cost control
2. ✅ **Policy Testing Framework** - Required for safe deployments

### Phase 2: Performance (Weeks 3-4)
3. ✅ **Semantic Caching** - Major cost/performance improvement
4. ✅ **Backend Load Balancing** - Multi-endpoint reliability

### Phase 3: Operations (Weeks 5-6)
5. ✅ **Observability Dashboard** - Operational visibility
6. ✅ **Multi-Tenancy** - SaaS enablement

---

## Success Metrics

### After Implementation

| Metric | Current | Target | Feature Responsible |
|--------|---------|--------|-------------------|
| **LLM Cost per 1K Requests** | $1.50 | $0.30 | Semantic Caching |
| **P95 Response Time (LLM)** | 800ms | <100ms | Semantic Caching |
| **Max Throughput** | 1K req/s | 5K req/s | Load Balancing |
| **Policy Test Coverage** | 0% | 95% | Testing Framework |
| **Multi-Customer Support** | No | Yes | Multi-Tenancy |
| **Competitive Gap vs Azure** | 40% | 80% | All Features |

---

## Competitive Position After Implementation

### Before
- ✅ Security & Compliance (OWASP, PII, audit)
- ❌ Token management
- ❌ Semantic caching
- ❌ Load balancing
- ⚠️ Basic observability

### After
- ✅ Security & Compliance (OWASP, PII, audit)
- ✅ Token management (TPM quotas)
- ✅ Semantic caching (cost optimization)
- ✅ Load balancing (multi-backend)
- ✅ Enterprise observability
- ✅ Multi-tenancy (SaaS ready)

**Result**: Close 60% of feature gap with Azure APIM while maintaining security-first advantage.

---

## Appendix: Quick Wins (Can Implement Today)

### 1. Request ID Tracing
```python
# app/main.py
import uuid

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### 2. Health Check with Dependencies
```python
@app.get("/health/detailed")
async def detailed_health():
    return {
        "status": "healthy",
        "checks": {
            "rules_loaded": len(rules_store.get("rules", [])) > 0,
            "redis": check_redis_connection(),
            "openai": check_openai_connection(),
            "disk_space": check_disk_space()
        }
    }
```

### 3. Request Body Size Limiting
```python
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    if request.headers.get("content-length"):
        if int(request.headers["content-length"]) > MAX_SIZE:
            return JSONResponse(
                {"error": "Request too large"},
                status_code=413
            )
    return await call_next(request)
```

---

**Next Steps**: Prioritize Phase 1 features (Token Limiting + Testing) for immediate implementation.

