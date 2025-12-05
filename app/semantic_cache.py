"""
Semantic caching for LLM responses using vector similarity.
Caches responses and retrieves them for semantically similar prompts.
"""
from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from config.loader import get_current_config

cache_dependencies_ok = True
cache_import_error: Optional[str] = None

try:  # numpy is required for cosine similarity
    import numpy as np  # type: ignore
except ImportError as exc:  # pragma: no cover - dependency optional
    cache_dependencies_ok = False
    np = None  # type: ignore
    cache_import_error = f"numpy import failed: {exc}"

if cache_dependencies_ok:
    try:  # Redis backend for distributed cache
        import redis  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency optional
        cache_dependencies_ok = False
        redis = None  # type: ignore
        cache_import_error = f"redis import failed: {exc}"

if cache_dependencies_ok:
    try:  # SentenceTransformer produces embeddings
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency optional
        cache_dependencies_ok = False
        SentenceTransformer = None  # type: ignore
        cache_import_error = f"sentence-transformers import failed: {exc}"


ESTIMATED_COST_PER_CALL = 0.02  # Rough cost avoidance per cached LLM call (USD)


@dataclass
class SemanticCacheConfig:
    """Runtime configuration extracted from Jimini config."""

    enabled: bool
    redis_url: str
    similarity_threshold: float
    ttl_seconds: int


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
        ttl_seconds: int = 3600,
    ) -> None:
        if not cache_dependencies_ok:
            raise RuntimeError(
                cache_import_error
                or "Redis and sentence-transformers required for semantic caching"
            )

        self.redis_client = redis.from_url(redis_url)  # type: ignore[arg-type]
        self.model = SentenceTransformer("all-MiniLM-L6-v2")  # type: ignore[call-arg]
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds

        self._lock = threading.Lock()
        self._metrics: Dict[str, Any] = {
            "lookups": 0,
            "hits": 0,
            "misses": 0,
            "stores": 0,
            "errors": 0,
            "sum_similarity": 0.0,
            "similarity_samples": 0,
            "last_error": None,
        }

    def _record(self, key: str, value: float = 1.0) -> None:
        with self._lock:
            if key in self._metrics:
                self._metrics[key] += value
            else:
                self._metrics[key] = value

    def _set_error(self, error: str) -> None:
        with self._lock:
            self._metrics["errors"] += 1
            self._metrics["last_error"] = error

    def get_embedding(self, text: str) -> "np.ndarray":
        """Generate embedding vector for text."""
        return self.model.encode(text)  # type: ignore[no-any-return]

    def cosine_similarity(self, vec1: "np.ndarray", vec2: "np.ndarray") -> float:
        """Calculate cosine similarity between vectors (defensive against zero norms)."""
        denom = float(np.linalg.norm(vec1) * np.linalg.norm(vec2))  # type: ignore[arg-type]
        if denom == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / denom)  # type: ignore[arg-type]

    def lookup(self, prompt: str, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Look up cached response for semantically similar prompt.

        Returns cached response if similarity >= threshold, else None.
        """
        self._record("lookups")

        try:
            prompt_embedding = self.get_embedding(prompt)
            cache_key_pattern = f"semantic_cache:{rule_id}:*"

            for cache_key in self.redis_client.scan_iter(match=cache_key_pattern):
                cached_data = self.redis_client.get(cache_key)
                if not cached_data:
                    continue

                cached = json.loads(cached_data.decode("utf-8"))
                cached_embedding = np.array(cached["embedding"], dtype=float)  # type: ignore[arg-type]

                similarity = self.cosine_similarity(prompt_embedding, cached_embedding)

                if similarity >= self.similarity_threshold:
                    self._record("hits")
                    self._record("sum_similarity", similarity)
                    self._record("similarity_samples")
                    return {
                        "response": cached["response"],
                        "similarity": float(similarity),
                        "cached_at": cached.get("timestamp"),
                        "cache_hit": True,
                    }

            self._record("misses")
        except Exception as exc:  # pragma: no cover - defensive path
            self._set_error(str(exc))
            return None

        return None

    def store(self, prompt: str, rule_id: str, response: str) -> None:
        """Store LLM response in the cache with its embedding."""
        try:
            prompt_embedding = self.get_embedding(prompt)
            prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
            cache_key = f"semantic_cache:{rule_id}:{prompt_hash}"

            cache_data = {
                "prompt": prompt,
                "embedding": prompt_embedding.tolist(),
                "response": response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            self.redis_client.setex(cache_key, self.ttl_seconds, json.dumps(cache_data))
            self._record("stores")
        except Exception as exc:  # pragma: no cover - defensive path
            self._set_error(str(exc))

    def get_metrics(self) -> Dict[str, Any]:
        """Expose metrics with derived values."""
        with self._lock:
            lookups = self._metrics.get("lookups", 0)
            hits = self._metrics.get("hits", 0)
            misses = self._metrics.get("misses", 0)
            stores = self._metrics.get("stores", 0)
            errors = self._metrics.get("errors", 0)
            sum_similarity = self._metrics.get("sum_similarity", 0.0)
            samples = self._metrics.get("similarity_samples", 0)
            last_error = self._metrics.get("last_error")

        hit_rate = float(hits) / float(lookups) if lookups else 0.0
        avg_similarity = float(sum_similarity) / float(samples) if samples else 0.0
        cost_savings = hits * ESTIMATED_COST_PER_CALL

        return {
            "enabled": True,
            "available": True,
            "lookups": int(lookups),
            "hits": int(hits),
            "misses": int(misses),
            "stores": int(stores),
            "errors": int(errors),
            "hit_rate": round(hit_rate, 4),
            "avg_similarity": round(avg_similarity, 4),
            "estimated_cost_savings_usd": round(cost_savings, 4),
            "similarity_threshold": self.similarity_threshold,
            "ttl_seconds": self.ttl_seconds,
            "last_error": last_error,
            "cache_backend": "redis",
        }


_semantic_cache: Optional[SemanticCache] = None
_cache_init_attempted = False
_cache_init_error: Optional[str] = None


def _load_runtime_config() -> SemanticCacheConfig:
    cfg = get_current_config()
    try:
        semantic_cfg = cfg.semantic_cache
    except AttributeError:
        return SemanticCacheConfig(False, "redis://localhost:6379", 0.95, 3600)

    return SemanticCacheConfig(
        enabled=semantic_cfg.enabled,
        redis_url=semantic_cfg.redis_url,
        similarity_threshold=float(semantic_cfg.similarity_threshold),
        ttl_seconds=int(semantic_cfg.ttl_seconds),
    )


def get_semantic_cache() -> Optional[SemanticCache]:
    """Get or initialize the semantic cache if the feature is enabled."""
    global _semantic_cache, _cache_init_attempted, _cache_init_error

    if _semantic_cache is not None:
        return _semantic_cache

    if _cache_init_attempted:
        return None

    config = _load_runtime_config()
    if not config.enabled:
        _cache_init_attempted = True
        _cache_init_error = "semantic caching disabled"
        return None

    if not cache_dependencies_ok:
        _cache_init_attempted = True
        _cache_init_error = cache_import_error or "semantic cache dependencies missing"
        print(f"Semantic cache not available: {_cache_init_error}")
        return None

    try:
        _semantic_cache = SemanticCache(
            redis_url=config.redis_url,
            similarity_threshold=config.similarity_threshold,
            ttl_seconds=config.ttl_seconds,
        )
    except Exception as exc:  # pragma: no cover - initialization failure
        _cache_init_attempted = True
        _cache_init_error = str(exc)
        print(f"Semantic cache initialization failed: {exc}")
        return None

    _cache_init_attempted = True
    _cache_init_error = None
    return _semantic_cache


def get_semantic_cache_metrics() -> Dict[str, Any]:
    """Expose semantic cache metrics for health and monitoring endpoints."""
    cache = get_semantic_cache()

    metrics: Dict[str, Any] = {
        "enabled": False,
        "available": False,
        "lookups": 0,
        "hits": 0,
        "misses": 0,
        "stores": 0,
        "errors": 0,
        "hit_rate": 0.0,
        "avg_similarity": 0.0,
        "estimated_cost_savings_usd": 0.0,
        "similarity_threshold": None,
        "ttl_seconds": None,
        "last_error": _cache_init_error or cache_import_error,
        "cache_backend": None,
    }

    config = _load_runtime_config()
    metrics["enabled"] = config.enabled

    if cache is None:
        metrics["available"] = False
        metrics["similarity_threshold"] = config.similarity_threshold
        metrics["ttl_seconds"] = config.ttl_seconds
        return metrics

    cache_metrics = cache.get_metrics()
    metrics.update(cache_metrics)
    return metrics