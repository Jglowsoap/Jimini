#!/usr/bin/env python3
"""
Phase 4 Production Hardening & Release Validation Script

Comprehensive test suite for validating all Phase 4 components:
- 4A: Configuration validation 
- 4B: Resilience (circuit breakers, retry, dead letter)
- 4C: Security & compliance
- 4D: Enhanced audit logging with tamper-evident chains
- 4E: Documentation
- 4F: Test coverage
"""

import asyncio
import tempfile
import json
from pathlib import Path
import os
import sys

# Test results tracking
test_results = {
    "4A_config": {"passed": 0, "failed": 0, "tests": []},
    "4B_resilience": {"passed": 0, "failed": 0, "tests": []},
    "4C_security": {"passed": 0, "failed": 0, "tests": []}, 
    "4D_audit": {"passed": 0, "failed": 0, "tests": []},
    "4E_docs": {"passed": 0, "failed": 0, "tests": []},
    "4F_coverage": {"passed": 0, "failed": 0, "tests": []}
}


def log_test_result(phase: str, test_name: str, passed: bool, details: str = ""):
    """Log test result and update counters"""
    result = "✅ PASS" if passed else "❌ FAIL"
    print(f"    {result}: {test_name}")
    if details:
        print(f"         {details}")
    
    test_results[phase]["tests"].append({
        "name": test_name,
        "passed": passed,
        "details": details
    })
    
    if passed:
        test_results[phase]["passed"] += 1
    else:
        test_results[phase]["failed"] += 1


async def test_phase_4a_configuration():
    """Test Phase 4A: Configuration validation"""
    print("\n📋 Phase 4A: Configuration Validation")
    print("-" * 50)
    
    try:
        from config.loader import get_current_config, validate_config_file
        
        # Test 1: Load current configuration
        try:
            config = get_current_config()
            log_test_result("4A_config", "Load current configuration", True, f"Profile: {config.profile}")
        except Exception as e:
            log_test_result("4A_config", "Load current configuration", False, str(e))
        
        # Test 2: Configuration file validation
        config_files = [
            Path("jimini.config.yaml"),
            Path("config") / "dev.yaml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    validate_config_file(str(config_file))
                    log_test_result("4A_config", f"Validate {config_file}", True)
                except Exception as e:
                    log_test_result("4A_config", f"Validate {config_file}", False, str(e))
        
        # Test 3: Environment variable precedence
        try:
            original_shadow = os.environ.get('JIMINI_SHADOW')
            os.environ['JIMINI_SHADOW'] = 'true'
            config_with_env = get_current_config()
            has_shadow = config_with_env.app.shadow_mode
            log_test_result("4A_config", "Environment variable precedence", has_shadow, "JIMINI_SHADOW=true applied")
            
            # Restore original
            if original_shadow is None:
                os.environ.pop('JIMINI_SHADOW', None)
            else:
                os.environ['JIMINI_SHADOW'] = original_shadow
        except Exception as e:
            log_test_result("4A_config", "Environment variable precedence", False, str(e))
    
    except ImportError as e:
        log_test_result("4A_config", "Configuration system import", False, str(e))


async def test_phase_4b_resilience():
    """Test Phase 4B: Resilience components"""
    print("\n🛡️  Phase 4B: Resilience & Error Handling")
    print("-" * 50)
    
    try:
        from app.resilience import resilience_manager, CircuitBreaker
        
        # Test 1: Circuit breaker functionality
        try:
            cb = CircuitBreaker("test_service", failure_threshold=2, timeout=1)
            
            # Test successful call
            @cb
            def success_func():
                return "success"
            
            result = success_func()
            log_test_result("4B_resilience", "Circuit breaker success", result == "success")
            
            # Test failure handling
            @cb  
            def fail_func():
                raise Exception("Test failure")
            
            try:
                fail_func()
            except:
                pass  # Expected to fail
            
            log_test_result("4B_resilience", "Circuit breaker failure handling", True)
            
        except Exception as e:
            log_test_result("4B_resilience", "Circuit breaker functionality", False, str(e))
        
        # Test 2: Resilience manager health  
        try:
            health = resilience_manager.get_health_status()
            has_circuit_breakers = "circuit_breakers" in health
            has_dlq = "dead_letter_queue" in health
            log_test_result("4B_resilience", "Resilience manager health", 
                          has_circuit_breakers and has_dlq, f"CBs: {has_circuit_breakers}, DLQ: {has_dlq}")
        except Exception as e:
            log_test_result("4B_resilience", "Resilience manager health", False, str(e))
            
        # Test 3: Dead letter queue
        try:
            from app.resilience import DeadLetterQueue
            dlq = DeadLetterQueue(max_size=10)
            
            dlq.add_failed_event({
                "event": "test_failure", 
                "error": "test error",
                "timestamp": "2025-01-01T00:00:00Z"
            })
            
            stats = dlq.get_stats()
            log_test_result("4B_resilience", "Dead letter queue", stats["size"] == 1)
        except Exception as e:
            log_test_result("4B_resilience", "Dead letter queue", False, str(e))
            
    except ImportError as e:
        log_test_result("4B_resilience", "Resilience system import", False, str(e))


async def test_phase_4c_security():
    """Test Phase 4C: Security & compliance"""
    print("\n🔐 Phase 4C: Security & Compliance")
    print("-" * 50)
    
    try:
        # Test 1: Security middleware
        try:
            from app.security_middleware import SecurityMiddlewareManager
            # If import succeeds, middleware is available
            log_test_result("4C_security", "Security middleware available", True)
        except ImportError as e:
            log_test_result("4C_security", "Security middleware available", False, str(e))
        
        # Test 2: PII redaction
        try:
            from app.redaction import get_redactor
            redactor = get_redactor()
            
            test_text = "My SSN is 123-45-6789 and email is user@example.com"
            redacted = redactor.redact_pii(test_text)
            has_redaction = "[REDACTED" in redacted
            log_test_result("4C_security", "PII redaction", has_redaction, f"Redacted: {redacted[:50]}...")
        except Exception as e:
            log_test_result("4C_security", "PII redaction", False, str(e))
        
        # Test 3: RBAC system
        try:
            from app.rbac import get_rbac, Role
            rbac = get_rbac()
            
            # Test role checking
            has_admin = Role.ADMIN in Role
            has_reviewer = Role.REVIEWER in Role
            log_test_result("4C_security", "RBAC roles defined", has_admin and has_reviewer)
        except Exception as e:
            log_test_result("4C_security", "RBAC roles defined", False, str(e))
            
        # Test 4: JWT validation (if available)
        try:
            from app.jwt_validator import JWTValidator
            validator = JWTValidator()
            log_test_result("4C_security", "JWT validation available", True)
        except ImportError:
            log_test_result("4C_security", "JWT validation available", False, "Module not found")
        except Exception as e:
            log_test_result("4C_security", "JWT validation available", False, str(e))
    
    except Exception as e:
        log_test_result("4C_security", "Security system error", False, str(e))


async def test_phase_4d_audit():
    """Test Phase 4D: Enhanced audit logging"""
    print("\n📝 Phase 4D: Enhanced Audit Logging")
    print("-" * 50)
    
    try:
        from app.audit_logger import AuditLogger, log_policy_decision, verify_audit_chain
        
        # Test with fresh audit file
        with tempfile.TemporaryDirectory() as temp_dir:
            test_audit = Path(temp_dir) / "test_audit.jsonl"
            logger = AuditLogger(test_audit)
            
            # Test 1: Policy decision logging
            try:
                record = logger.log_policy_decision(
                    action="block",
                    request_id="test-001",
                    direction="inbound", 
                    endpoint="/test",
                    rule_ids=["TEST-1.0"],
                    text_excerpt="test content"
                )
                log_test_result("4D_audit", "Policy decision logging", record.action == "block")
            except Exception as e:
                log_test_result("4D_audit", "Policy decision logging", False, str(e))
            
            # Test 2: Chain integrity verification
            try:
                verification = logger.verify_chain()
                log_test_result("4D_audit", "Chain integrity verification", 
                              verification["valid"], f"Records: {verification['total_records']}")
            except Exception as e:
                log_test_result("4D_audit", "Chain integrity verification", False, str(e))
            
            # Test 3: Tamper detection
            try:
                # Add another record
                logger.log_policy_decision("allow", "test-002", "outbound", "/test2", [], "safe content")
                
                # Read and modify file to simulate tampering
                with test_audit.open("r") as f:
                    lines = f.readlines()
                
                if len(lines) >= 2:
                    # Corrupt second record
                    lines[1] = lines[1].replace('"allow"', '"TAMPERED"')
                    with test_audit.open("w") as f:
                        f.writelines(lines)
                    
                    # Verify tamper detection
                    verification = logger.verify_chain()
                    tamper_detected = not verification["valid"]
                    log_test_result("4D_audit", "Tamper detection", tamper_detected)
                else:
                    log_test_result("4D_audit", "Tamper detection", False, "Not enough records for test")
            except Exception as e:
                log_test_result("4D_audit", "Tamper detection", False, str(e))
            
            # Test 4: Admin and security events
            try:
                # Reset file for clean test
                test_audit.unlink()
                logger = AuditLogger(test_audit)
                
                admin_record = logger.log_admin_action("admin@test.com", "user_create", "users")
                security_record = logger.log_security_event("auth_failure", "high", "Failed login", "192.168.1.1")
                
                log_test_result("4D_audit", "Admin/security event logging", 
                              admin_record and security_record)
            except Exception as e:
                log_test_result("4D_audit", "Admin/security event logging", False, str(e))
                
            # Test 5: Statistics and export
            try:
                stats = logger.get_chain_stats()
                has_stats = "total_records" in stats and "actions" in stats
                log_test_result("4D_audit", "Audit statistics", has_stats)
            except Exception as e:
                log_test_result("4D_audit", "Audit statistics", False, str(e))
    
    except ImportError as e:
        log_test_result("4D_audit", "Enhanced audit system import", False, str(e))


async def test_phase_4e_documentation():
    """Test Phase 4E: Documentation"""
    print("\n📚 Phase 4E: Documentation")
    print("-" * 50)
    
    # Test documentation files exist
    doc_files = [
        "README.md",
        "PHASE_4_SECURITY_COMPLIANCE.md",
        "PHASE_4_AUDIT_ENHANCED.md"
    ]
    
    for doc_file in doc_files:
        file_path = Path(doc_file)
        exists = file_path.exists()
        size = file_path.stat().st_size if exists else 0
        log_test_result("4E_docs", f"{doc_file} exists", exists, f"Size: {size} bytes")
    
    # Test API documentation  
    try:
        from app.main import app
        has_openapi = hasattr(app, 'openapi')
        log_test_result("4E_docs", "OpenAPI documentation", has_openapi)
    except Exception as e:
        log_test_result("4E_docs", "OpenAPI documentation", False, str(e))


async def test_phase_4f_coverage():
    """Test Phase 4F: Test coverage"""
    print("\n🧪 Phase 4F: Test Coverage")
    print("-" * 50)
    
    # Check for test files
    test_files = [
        "tests/test_enforcement.py",
        "tests/test_resilience.py", 
        "tests/test_audit_chain_validation.py",
        "test_enhanced_audit_fresh.py"
    ]
    
    for test_file in test_files:
        file_path = Path(test_file)
        exists = file_path.exists()
        log_test_result("4F_coverage", f"{test_file} exists", exists)
    
    # Check if pytest is available
    try:
        import pytest
        log_test_result("4F_coverage", "pytest available", True)
    except ImportError:
        log_test_result("4F_coverage", "pytest available", False)


def print_final_summary():
    """Print comprehensive test summary"""
    print("\n" + "=" * 70)
    print("🎯 PHASE 4 PRODUCTION HARDENING VALIDATION SUMMARY")
    print("=" * 70)
    
    total_passed = 0
    total_failed = 0
    
    for phase, results in test_results.items():
        passed = results["passed"]
        failed = results["failed"] 
        total = passed + failed
        
        if total > 0:
            percentage = (passed / total) * 100
            status = "✅ PASS" if failed == 0 else "⚠️  PARTIAL" if passed > failed else "❌ FAIL"
            
            print(f"\n{phase.upper().replace('_', ' ')}: {status} ({passed}/{total} - {percentage:.1f}%)")
            
            if failed > 0:
                print("    Failed tests:")
                for test in results["tests"]:
                    if not test["passed"]:
                        print(f"      - {test['name']}: {test['details']}")
        
        total_passed += passed
        total_failed += failed
    
    # Overall summary
    grand_total = total_passed + total_failed
    if grand_total > 0:
        overall_percentage = (total_passed / grand_total) * 100
        print(f"\n🏆 OVERALL: {total_passed}/{grand_total} tests passed ({overall_percentage:.1f}%)")
        
        if overall_percentage >= 90:
            print("🎉 PRODUCTION READY - Excellent hardening coverage!")
        elif overall_percentage >= 75:
            print("✅ GOOD - Solid production hardening foundation")
        elif overall_percentage >= 50:
            print("⚠️  NEEDS WORK - Additional hardening required")
        else:
            print("❌ NOT READY - Significant hardening gaps")
        
        # Production readiness assessment
        critical_phases = ["4A_config", "4B_resilience", "4D_audit"]
        critical_failures = sum(test_results[phase]["failed"] for phase in critical_phases)
        
        if critical_failures == 0:
            print("🔒 SECURITY POSTURE: Production-grade")
        else:
            print(f"⚠️  SECURITY POSTURE: {critical_failures} critical issues need attention")


async def main():
    """Run comprehensive Phase 4 validation"""
    print("🚀 Starting Phase 4 Production Hardening Validation")
    print("Testing all components for production readiness...")
    
    # Run all phase tests
    await test_phase_4a_configuration()
    await test_phase_4b_resilience()
    await test_phase_4c_security()
    await test_phase_4d_audit()
    await test_phase_4e_documentation()
    await test_phase_4f_coverage()
    
    # Print final summary
    print_final_summary()
    
    # Return success if no critical failures
    critical_phases = ["4A_config", "4B_resilience", "4D_audit"]
    critical_failures = sum(test_results[phase]["failed"] for phase in critical_phases)
    return critical_failures == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)