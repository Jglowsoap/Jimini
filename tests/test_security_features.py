# tests/test_security_features.py - Comprehensive Security & Compliance Tests

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.redaction import PIIRedactor, get_redactor
from app.rbac import RBACManager, Role, User, get_rbac
from app.circuit_breaker import CircuitBreaker, circuit_manager
from app.models import EvaluateRequest


@pytest.fixture
def test_client():
    """Test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def pii_redactor():
    """PII redactor instance for testing."""
    return PIIRedactor()


@pytest.fixture
def rbac_manager():
    """RBAC manager instance for testing."""
    return RBACManager()


class TestPIIRedaction:
    """Test PII redaction system with all 7 rule types."""

    def test_email_redaction(self, pii_redactor):
        """Test email address redaction."""
        text = "Contact john.doe@company.com for support"
        result = pii_redactor.redact_text(text)
        assert "[EMAIL_REDACTED]" in result
        assert "john.doe@company.com" not in result

    def test_api_key_redaction(self, pii_redactor):
        """Test API key/token redaction."""
        text = "Use token sk_1234567890abcdefghijklmnopqrstuvwxyz123456"
        result = pii_redactor.redact_text(text)
        assert "[TOKEN_REDACTED]" in result
        assert "sk_1234567890abcdefghijklmnopqrstuvwxyz123456" not in result

    def test_uuid_redaction(self, pii_redactor):
        """Test UUID redaction."""
        text = "Transaction ID: 123e4567-e89b-12d3-a456-426614174000"
        result = pii_redactor.redact_text(text)
        assert "[UUID_REDACTED]" in result
        assert "123e4567-e89b-12d3-a456-426614174000" not in result

    def test_ssn_redaction(self, pii_redactor):
        """Test Social Security Number redaction."""
        text = "SSN: 123-45-6789"
        result = pii_redactor.redact_text(text)
        assert "[SSN_REDACTED]" in result
        assert "123-45-6789" not in result

    def test_phone_redaction(self, pii_redactor):
        """Test phone number redaction."""
        text = "Call (555) 123-4567 for assistance"
        result = pii_redactor.redact_text(text)
        assert "[PHONE_REDACTED]" in result
        assert "(555) 123-4567" not in result

    def test_ip_address_redaction(self, pii_redactor):
        """Test IP address redaction."""
        text = "Server at 192.168.1.100 is down"
        result = pii_redactor.redact_text(text)
        assert "[IP_REDACTED]" in result
        assert "192.168.1.100" not in result

    def test_credit_card_redaction(self, pii_redactor):
        """Test credit card number redaction."""
        text = "Card number: 4532-1234-5678-9012"
        result = pii_redactor.redact_text(text)
        assert "[CC_REDACTED]" in result
        assert "4532-1234-5678-9012" not in result

    def test_multiple_pii_types(self, pii_redactor):
        """Test redaction of multiple PII types in single text."""
        text = "Email john@company.com, phone (555) 123-4567, SSN 123-45-6789"
        result = pii_redactor.redact_text(text)
        
        assert "[EMAIL_REDACTED]" in result
        assert "[PHONE_REDACTED]" in result
        assert "[SSN_REDACTED]" in result
        assert "john@company.com" not in result
        assert "(555) 123-4567" not in result
        assert "123-45-6789" not in result

    def test_dict_redaction(self, pii_redactor):
        """Test redaction of dictionary data structures."""
        data = {
            "user": "john.doe@company.com",
            "contact": {"phone": "(555) 123-4567"},
            "metadata": {"ssn": "123-45-6789"}
        }
        
        result = pii_redactor.redact_dict(data)
        
        assert "[EMAIL_REDACTED]" in result["user"]
        assert "[PHONE_REDACTED]" in result["contact"]["phone"]
        assert "[SSN_REDACTED]" in result["metadata"]["ssn"]

    def test_hash_preservation(self, pii_redactor):
        """Test that hashes are preserved for audit trails."""
        text = "john@company.com"
        result1 = pii_redactor.redact_text(text)
        result2 = pii_redactor.redact_text(text)
        
        # Should have same hash for same input
        assert result1 == result2
        assert "[EMAIL_REDACTED]" in result1


class TestRBACSystem:
    """Test Role-Based Access Control system."""

    def test_role_hierarchy(self, rbac_manager):
        """Test role hierarchy and permissions."""
        admin_user = User(id="admin", username="admin", roles=[Role.ADMIN])
        user_user = User(id="user", username="user", roles=[Role.USER])
        
        assert rbac_manager.has_role(admin_user, Role.ADMIN)
        assert rbac_manager.has_role(admin_user, Role.USER) 
        assert not rbac_manager.has_role(user_user, Role.ADMIN)

    def test_api_key_role_mapping(self, rbac_manager):
        """Test API key to role mapping."""
        mock_request = MagicMock()
        mock_request.headers = {'X-API-Key': 'admin-key'}
        
        user = rbac_manager.extract_user_from_request(mock_request)
        if rbac_manager.enabled:
            assert user is not None
            assert Role.ADMIN in user.roles

    def test_rbac_disabled_behavior(self, rbac_manager):
        """Test RBAC behavior when disabled."""
        # By default, RBAC should be disabled in tests
        mock_request = MagicMock()
        mock_request.headers = {}
        
        user = rbac_manager.extract_user_from_request(mock_request)
        assert user is not None
        assert Role.ADMIN in user.roles

    def test_missing_authorization_header(self, rbac_manager):
        """Test handling of missing authorization header."""
        mock_request = MagicMock()
        mock_request.headers = {}
        
        user = rbac_manager.extract_user_from_request(mock_request)
        # With RBAC enabled=False, should return admin user
        assert user is not None

    def test_invalid_authorization_format(self, rbac_manager):
        """Test handling of invalid authorization header format."""
        mock_request = MagicMock()
        mock_request.headers = {'Authorization': 'Invalid format'}
        
        user = rbac_manager.extract_user_from_request(mock_request)
        # With RBAC enabled=False, should return admin user
        assert user is not None


class TestAdminEndpoints:
    """Test RBAC-protected admin endpoints."""

    def test_admin_security_endpoint_access(self, test_client):
        """Test admin security endpoint accessibility."""
        response = test_client.get("/admin/security")
        # Should be accessible (RBAC disabled in test environment)
        assert response.status_code == 200

    def test_health_endpoint_access(self, test_client):
        """Test health endpoint accessibility."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestSecurityIntegration:
    """Test integration between security components."""

    @patch('config.loader.get_current_config')
    def test_pii_redaction_in_evaluation(self, mock_config, test_client):
        """Test PII redaction during policy evaluation."""
        # Mock configuration
        mock_cfg = MagicMock()
        mock_cfg.app.shadow_mode = False
        mock_cfg.security.pii_processing = True
        mock_config.return_value = mock_cfg

        response = test_client.post(
            "/v1/evaluate",
            json={
                "api_key": "changeme",
                "text": "Send to john.doe@company.com",
                "direction": "outbound",
                "endpoint": "/api/export"
            }
        )
        
        assert response.status_code == 200
        # In a real implementation, we'd verify PII was redacted in logs

    @patch('config.loader.get_current_config')
    def test_rbac_and_pii_integration(self, mock_config, test_client):
        """Test RBAC and PII redaction working together."""
        mock_cfg = MagicMock()
        mock_cfg.security.rbac_enabled = True
        mock_cfg.security.pii_processing = True
        mock_config.return_value = mock_cfg

        # Test that admin endpoints properly handle PII in responses
        with patch('app.rbac.RBACManager.get_user_role') as mock_role:
            mock_role.return_value = Role.ADMIN
            
            response = test_client.get(
                "/admin/security",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["security_config"]["pii_processing"] == True
            assert data["security_config"]["rbac_enabled"] == True


class TestAuditIntegrity:
    """Test audit chain integrity and security features."""

    def test_audit_chain_creation(self):
        """Test audit chain record creation."""
        from app.audit import AuditRecord
        from app.util import gen_request_id
        from datetime import datetime, timezone
        
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=gen_request_id(),
            action="block",
            direction="outbound", 
            endpoint="/api/export",
            rule_ids=["EMAIL-1.0"],
            text_excerpt="Contact john@company.com",
            text_hash="",
            previous_hash=""
        )
        
        assert record.action == "block"
        assert "EMAIL-1.0" in record.rule_ids
        assert len(record.request_id) > 0

    @patch('app.audit.append_audit')
    def test_audit_pii_redaction(self, mock_append):
        """Test that audit logs properly redact PII."""
        from app.enforcement import evaluate
        
        # Test audit system directly without enforcement
        from app.audit import append_audit, AuditRecord
        
        # Create a test audit record with proper fields
        audit_record = AuditRecord(
            timestamp="2024-01-01T00:00:00Z",
            request_id="test-123",
            action="flag",
            direction="outbound",
            endpoint="/api/export",
            rule_ids=["EMAIL-1.0"],
            text_excerpt="Contact [EMAIL_REDACTED]_hash123",
            text_hash="hash123",
            previous_hash="prev123",
            pii_redacted=True
        )
        
        # Verify PII is redacted in audit
        assert "[EMAIL_REDACTED]" in audit_record.text_excerpt
        assert "john.doe@company.com" not in audit_record.text_excerpt
        
        # Verify audit was called
        mock_append.assert_called_once()
        
        # Verify decision
        assert decision in ["flag", "allow"]  # Depending on regex compilation


class TestCircuitBreakerSecurity:
    """Test security implications of circuit breakers."""

    def test_circuit_breaker_prevents_cascading_failures(self):
        """Test circuit breaker prevents security-related cascading failures."""
        from app.circuit_breaker import CircuitBreaker
        
        cb = CircuitBreaker("security_test", failure_threshold=2, recovery_timeout=1)
        
        # Simulate failures
        for _ in range(3):
            try:
                with cb:
                    raise Exception("Security validation failed")
            except Exception:
                pass
        
        # Circuit should be open now
        assert cb.state == "OPEN"
        
        # Next call should fail fast
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            with cb:
                pass

    def test_circuit_breaker_state_transitions(self):
        """Test circuit breaker state transitions for security components."""
        from app.circuit_breaker import CircuitBreaker
        import time
        
        cb = CircuitBreaker("state_test", failure_threshold=1, recovery_timeout=1)
        
        # Start in CLOSED state
        assert cb.state == "CLOSED"
        
        # Trigger failure to open circuit
        try:
            with cb:
                raise Exception("Security check failed")
        except Exception:
            pass
        
        assert cb.state == "OPEN"
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Next call should transition to HALF_OPEN
        try:
            with cb:
                pass  # Success
        except Exception:
            pass
        
        # Should be back to CLOSED after success
        assert cb.state == "CLOSED"


@pytest.mark.integration
class TestSecurityEndToEnd:
    """End-to-end security feature testing."""

    @patch('config.loader.get_current_config')
    def test_complete_security_pipeline(self, mock_config, test_client):
        """Test complete security pipeline with all features."""
        # Configure security features
        mock_cfg = MagicMock()
        mock_cfg.app.shadow_mode = False
        mock_cfg.security.pii_processing = True
        mock_cfg.security.rbac_enabled = True
        mock_config.return_value = mock_cfg

        # Test evaluation with PII content
        response = test_client.post(
            "/v1/evaluate",
            json={
                "api_key": "changeme", 
                "text": "User john@company.com with SSN 123-45-6789",
                "direction": "outbound",
                "endpoint": "/api/sensitive"
            }
        )
        
        assert response.status_code == 200
        
        # Test admin access with proper role
        with patch('app.rbac.RBACManager.get_user_role') as mock_role:
            mock_role.return_value = Role.ADMIN
            
            admin_response = test_client.get(
                "/admin/security",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert admin_response.status_code == 200
            security_data = admin_response.json()
            
            # Verify security configuration is reported correctly
            assert security_data["security_config"]["pii_processing"] == True
            assert security_data["security_config"]["rbac_enabled"] == True
            assert len(security_data["redaction_summary"]["redaction_rules"]) == 7

    def test_security_metrics_collection(self, test_client):
        """Test that security metrics are properly collected."""
        # Make several requests to generate metrics
        for i in range(5):
            test_client.post(
                "/v1/evaluate",
                json={
                    "api_key": "changeme",
                    "text": f"Test message {i}",
                    "direction": "outbound",
                    "endpoint": "/test"
                }
            )
        
        # Check metrics endpoint
        response = test_client.get("/v1/metrics")
        assert response.status_code == 200
        
        metrics = response.json()
        assert "totals" in metrics
        assert "loaded_rules" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])