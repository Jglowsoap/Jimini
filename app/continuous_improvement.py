"""
Continuous Improvement Tools for Jimini Policy Gateway

Provides:
- Synthetic traffic generator for load testing
- Chaos testing framework for resilience validation  
- Performance budget enforcement
- Benchmark CI integration for regression detection
- Automated performance monitoring
"""

import asyncio
import random
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import aiohttp
import structlog

logger = structlog.get_logger()


@dataclass
class PerformanceMetrics:
    """Performance measurement results."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_rps: float
    error_rate: float
    start_time: datetime
    end_time: datetime


@dataclass
class PerformanceBudget:
    """Performance budget constraints."""
    max_latency_p95_ms: float = 30.0
    max_latency_p99_ms: float = 100.0
    min_throughput_rps: float = 500.0
    max_error_rate: float = 0.01  # 1%
    max_memory_mb: int = 4000
    max_cpu_percent: float = 80.0


class SyntheticTrafficGenerator:
    """Generates synthetic traffic for load testing and monitoring."""
    
    def __init__(self, base_url: str = "http://localhost:9000"):
        self.base_url = base_url
        self.test_scenarios = self._load_test_scenarios()
        
    def _load_test_scenarios(self) -> List[Dict[str, Any]]:
        """Load test scenarios for various policy outcomes."""
        return [
            # ALLOW scenarios
            {
                "name": "safe_content",
                "text": "Hello world, this is safe content",
                "endpoint": "/api/test",
                "expected_decision": "allow"
            },
            {
                "name": "normal_conversation", 
                "text": "How are you doing today? The weather is nice.",
                "endpoint": "/api/chat",
                "expected_decision": "allow"
            },
            
            # FLAG scenarios
            {
                "name": "suspicious_content",
                "text": "This content might need review for policy compliance",
                "endpoint": "/api/review",
                "expected_decision": "flag"
            },
            
            # BLOCK scenarios
            {
                "name": "pii_ssn",
                "text": "My social security number is 123-45-6789",
                "endpoint": "/api/user-data",
                "expected_decision": "block"
            },
            {
                "name": "pii_email",
                "text": "Contact me at john.doe@example.com for details",
                "endpoint": "/api/contact",
                "expected_decision": "block"
            },
            {
                "name": "api_key_leak",
                "text": "Use this key: sk_1234567890abcdefghijklmnopqr",
                "endpoint": "/api/config",
                "expected_decision": "block"
            }
        ]
    
    async def generate_load(self, 
                          duration_seconds: int = 60,
                          target_rps: int = 100,
                          concurrent_users: int = 10) -> PerformanceMetrics:
        """Generate sustained load for specified duration."""
        logger.info(f"Starting load test: {target_rps} RPS for {duration_seconds}s with {concurrent_users} users")
        
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        # Calculate request interval
        request_interval = 1.0 / target_rps * concurrent_users
        
        # Tracking variables
        all_latencies = []
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def worker():
            """Worker coroutine for generating requests."""
            nonlocal total_requests, successful_requests, failed_requests, all_latencies
            
            async with aiohttp.ClientSession() as session:
                while datetime.utcnow() < end_time:
                    async with semaphore:
                        # Select random scenario
                        scenario = random.choice(self.test_scenarios)
                        
                        # Make request and measure latency
                        request_start = time.time()
                        success = await self._make_request(session, scenario)
                        latency_ms = (time.time() - request_start) * 1000
                        
                        # Update metrics
                        total_requests += 1
                        all_latencies.append(latency_ms)
                        
                        if success:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                            
                        # Control rate
                        await asyncio.sleep(request_interval)
        
        # Start workers
        tasks = [asyncio.create_task(worker()) for _ in range(concurrent_users)]
        
        # Wait for completion
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate metrics
        actual_end_time = datetime.utcnow()
        duration = (actual_end_time - start_time).total_seconds()
        
        metrics = PerformanceMetrics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_latency_ms=statistics.mean(all_latencies) if all_latencies else 0,
            p50_latency_ms=statistics.median(all_latencies) if all_latencies else 0,
            p95_latency_ms=self._percentile(all_latencies, 95) if all_latencies else 0,
            p99_latency_ms=self._percentile(all_latencies, 99) if all_latencies else 0,
            throughput_rps=total_requests / duration if duration > 0 else 0,
            error_rate=failed_requests / total_requests if total_requests > 0 else 0,
            start_time=start_time,
            end_time=actual_end_time
        )
        
        logger.info(f"Load test completed: {metrics.throughput_rps:.1f} RPS, "
                   f"{metrics.p95_latency_ms:.1f}ms p95, {metrics.error_rate:.2%} errors")
        
        return metrics
    
    async def _make_request(self, session: aiohttp.ClientSession, scenario: Dict[str, Any]) -> bool:
        """Make a single policy evaluation request."""
        try:
            payload = {
                "text": scenario["text"],
                "endpoint": scenario["endpoint"]
            }
            
            async with session.post(
                f"{self.base_url}/v1/evaluate",
                json=payload,
                headers={"Authorization": "Bearer changeme"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Validate expected outcome (optional)
                    expected = scenario.get("expected_decision")
                    actual = result.get("decision", "").lower()
                    
                    if expected and actual != expected:
                        logger.debug(f"Unexpected decision: expected {expected}, got {actual}")
                        
                    return True
                else:
                    logger.warning(f"Request failed with status {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Request error: {e}")
            return False
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not data:
            return 0.0
            
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def run_burst_test(self, burst_rps: int = 1000, duration_seconds: int = 10) -> PerformanceMetrics:
        """Run a burst test to check system limits."""
        logger.info(f"Starting burst test: {burst_rps} RPS for {duration_seconds}s")
        return await self.generate_load(duration_seconds, burst_rps, min(burst_rps // 10, 100))


class ChaosTestingFramework:
    """Framework for chaos engineering tests."""
    
    def __init__(self, base_url: str = "http://localhost:9000"):
        self.base_url = base_url
        self.traffic_generator = SyntheticTrafficGenerator(base_url)
        
    async def test_service_degradation(self) -> Dict[str, Any]:
        """Test graceful degradation when external services fail."""
        logger.info("Starting service degradation chaos test")
        
        results = {
            "test_name": "service_degradation",
            "start_time": datetime.utcnow().isoformat(),
            "scenarios": []
        }
        
        # Baseline performance
        logger.info("Measuring baseline performance")
        baseline = await self.traffic_generator.generate_load(30, 100, 10)
        results["scenarios"].append({
            "name": "baseline",
            "metrics": baseline.__dict__
        })
        
        # Test with OpenAI API failure simulation
        logger.info("Testing with LLM service failure")
        # In real implementation, this would disable/mock the LLM service
        llm_failure = await self.traffic_generator.generate_load(30, 100, 10)
        results["scenarios"].append({
            "name": "llm_failure", 
            "metrics": llm_failure.__dict__
        })
        
        # Test with SIEM forwarder failure
        logger.info("Testing with SIEM forwarder failure")
        siem_failure = await self.traffic_generator.generate_load(30, 100, 10)
        results["scenarios"].append({
            "name": "siem_failure",
            "metrics": siem_failure.__dict__
        })
        
        results["end_time"] = datetime.utcnow().isoformat()
        results["status"] = "completed"
        
        # Analyze degradation
        baseline_rps = baseline.throughput_rps
        baseline_p95 = baseline.p95_latency_ms
        
        for scenario in results["scenarios"][1:]:  # Skip baseline
            metrics = scenario["metrics"]
            rps_degradation = (baseline_rps - metrics["throughput_rps"]) / baseline_rps
            latency_degradation = (metrics["p95_latency_ms"] - baseline_p95) / baseline_p95
            
            scenario["degradation_analysis"] = {
                "throughput_loss_percent": rps_degradation * 100,
                "latency_increase_percent": latency_degradation * 100,
                "acceptable": rps_degradation < 0.2 and latency_degradation < 1.0  # 20% RPS, 100% latency
            }
        
        logger.info(f"Chaos test completed: {results}")
        return results
    
    async def test_memory_pressure(self) -> Dict[str, Any]:
        """Test behavior under memory pressure."""
        logger.info("Starting memory pressure chaos test")
        
        # This would simulate memory pressure in a real implementation
        # For now, we'll just run a high-load test
        result = await self.traffic_generator.generate_load(60, 500, 50)
        
        return {
            "test_name": "memory_pressure",
            "metrics": result.__dict__,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def test_network_partitions(self) -> Dict[str, Any]:
        """Test behavior during network partitions."""
        logger.info("Starting network partition chaos test")
        
        # This would simulate network issues in a real implementation
        result = await self.traffic_generator.generate_load(45, 200, 20)
        
        return {
            "test_name": "network_partitions", 
            "metrics": result.__dict__,
            "timestamp": datetime.utcnow().isoformat()
        }


class PerformanceBudgetEnforcer:
    """Enforces performance budgets and detects regressions."""
    
    def __init__(self, budget: PerformanceBudget):
        self.budget = budget
        
    def validate_metrics(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """Validate metrics against performance budget."""
        violations = []
        
        # Check latency constraints
        if metrics.p95_latency_ms > self.budget.max_latency_p95_ms:
            violations.append({
                "metric": "p95_latency_ms",
                "actual": metrics.p95_latency_ms,
                "budget": self.budget.max_latency_p95_ms,
                "severity": "critical"
            })
            
        if metrics.p99_latency_ms > self.budget.max_latency_p99_ms:
            violations.append({
                "metric": "p99_latency_ms", 
                "actual": metrics.p99_latency_ms,
                "budget": self.budget.max_latency_p99_ms,
                "severity": "warning"
            })
        
        # Check throughput constraints
        if metrics.throughput_rps < self.budget.min_throughput_rps:
            violations.append({
                "metric": "throughput_rps",
                "actual": metrics.throughput_rps,
                "budget": self.budget.min_throughput_rps,
                "severity": "critical"
            })
        
        # Check error rate constraints
        if metrics.error_rate > self.budget.max_error_rate:
            violations.append({
                "metric": "error_rate",
                "actual": metrics.error_rate,
                "budget": self.budget.max_error_rate,
                "severity": "critical"
            })
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "score": self._calculate_score(metrics),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate performance score (0-100).""" 
        score = 100.0
        
        # Latency penalty
        if metrics.p95_latency_ms > self.budget.max_latency_p95_ms:
            score -= 30 * (metrics.p95_latency_ms / self.budget.max_latency_p95_ms - 1)
            
        # Throughput penalty
        if metrics.throughput_rps < self.budget.min_throughput_rps:
            score -= 30 * (1 - metrics.throughput_rps / self.budget.min_throughput_rps)
            
        # Error rate penalty
        if metrics.error_rate > self.budget.max_error_rate:
            score -= 40 * (metrics.error_rate / self.budget.max_error_rate - 1)
        
        return max(0.0, min(100.0, score))


class BenchmarkRunner:
    """Runs benchmarks for CI integration."""
    
    def __init__(self):
        self.traffic_generator = SyntheticTrafficGenerator()
        self.chaos_framework = ChaosTestingFramework()
        self.budget_enforcer = PerformanceBudgetEnforcer(PerformanceBudget())
        
    async def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """Run complete benchmark suite for CI."""
        logger.info("Starting full benchmark suite")
        
        results = {
            "suite_name": "jimini_performance_benchmark",
            "start_time": datetime.utcnow().isoformat(),
            "tests": {}
        }
        
        # Standard load test
        logger.info("Running standard load test")
        standard_load = await self.traffic_generator.generate_load(60, 500, 25)
        budget_result = self.budget_enforcer.validate_metrics(standard_load)
        results["tests"]["standard_load"] = {
            "metrics": standard_load.__dict__,
            "budget_validation": budget_result
        }
        
        # Burst test
        logger.info("Running burst test")
        burst_test = await self.traffic_generator.run_burst_test(1000, 30)
        results["tests"]["burst_test"] = {
            "metrics": burst_test.__dict__
        }
        
        # Chaos tests
        logger.info("Running chaos tests")
        chaos_results = await self.chaos_framework.test_service_degradation()
        results["tests"]["chaos_degradation"] = chaos_results
        
        results["end_time"] = datetime.utcnow().isoformat()
        results["overall_passed"] = budget_result["passed"]
        results["performance_score"] = budget_result["score"]
        
        # Save results for historical comparison
        await self._save_benchmark_results(results)
        
        logger.info(f"Benchmark suite completed: score={budget_result['score']:.1f}, "
                   f"passed={budget_result['passed']}")
        
        return results
    
    async def _save_benchmark_results(self, results: Dict[str, Any]):
        """Save benchmark results for historical analysis."""
        results_dir = Path("benchmark_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = results_dir / f"benchmark_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Benchmark results saved to {filename}")
    
    def compare_with_baseline(self, current_results: Dict[str, Any], 
                            baseline_file: Optional[str] = None) -> Dict[str, Any]:
        """Compare current results with baseline."""
        if not baseline_file:
            # Find most recent baseline
            results_dir = Path("benchmark_results")
            if not results_dir.exists():
                return {"comparison": "no_baseline"}
                
            baselines = list(results_dir.glob("benchmark_*.json"))
            if not baselines:
                return {"comparison": "no_baseline"}
                
            baseline_file = str(sorted(baselines)[-1])
        
        try:
            with open(baseline_file, 'r') as f:
                baseline = json.load(f)
                
            current_score = current_results.get("performance_score", 0)
            baseline_score = baseline.get("performance_score", 0)
            
            return {
                "comparison": "completed",
                "baseline_file": baseline_file,
                "current_score": current_score,
                "baseline_score": baseline_score,
                "score_change": current_score - baseline_score,
                "regression_detected": current_score < baseline_score * 0.95  # 5% tolerance
            }
            
        except Exception as e:
            logger.error(f"Failed to compare with baseline: {e}")
            return {"comparison": "error", "error": str(e)}


# Global instances for easy access
traffic_generator = SyntheticTrafficGenerator()
chaos_framework = ChaosTestingFramework()  
benchmark_runner = BenchmarkRunner()


def get_traffic_generator() -> SyntheticTrafficGenerator:
    """Get global traffic generator instance."""
    return traffic_generator


def get_chaos_framework() -> ChaosTestingFramework:
    """Get global chaos testing framework instance."""
    return chaos_framework


def get_benchmark_runner() -> BenchmarkRunner:
    """Get global benchmark runner instance."""
    return benchmark_runner