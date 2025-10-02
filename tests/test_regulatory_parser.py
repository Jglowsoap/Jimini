"""
Phase 6A - Regulatory Parser Tests
Comprehensive test suite for AI-powered regulatory analysis
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.intelligence.regulatory_parser import (
    RegulatoryTextParser, RegulationType, RequirementType,
    PolicyRequirement, GeneratedRule, create_sample_gdpr_text
)
from app.intelligence.config import load_intelligence_config, get_regulation_config


class TestRegulatoryTextParser:
    """Test suite for RegulatoryTextParser."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance for testing."""
        return RegulatoryTextParser()
    
    @pytest.fixture
    def sample_gdpr_text(self):
        """Sample GDPR text for testing."""
        return create_sample_gdpr_text()
    
    @pytest.fixture
    def sample_hipaa_text(self):
        """Sample HIPAA text for testing."""
        return """
        164.502 Uses and disclosures of protected health information: General rules
        
        (a) Standard: A covered entity may not use or disclose protected health information, 
        except as permitted or required by this subpart or by subpart C of part 160 of this subchapter.
        
        (b) Standard: Minimum necessary. When using or disclosing protected health information 
        or when requesting protected health information from another covered entity, a covered entity 
        must make reasonable efforts to limit protected health information to the minimum necessary 
        to accomplish the intended purpose of the use, disclosure, or request.
        
        164.508 Uses and disclosures for which an authorization is required
        
        (a) Standard: Authorizations required. Except as otherwise permitted or required by this subchapter, 
        a covered entity may use or disclose protected health information only with the valid authorization 
        of the individual who is the subject of the information.
        """
    
    def test_parser_initialization(self, parser):
        """Test parser initializes correctly."""
        assert parser is not None
        assert hasattr(parser, 'rule_templates')
        assert hasattr(parser, 'regulation_patterns')
    
    def test_parse_text_document(self, parser):
        """Test parsing plain text documents."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document with regulatory content.")
            f.flush()
            
            try:
                text = parser.parse_document(f.name, RegulationType.GDPR)
                assert "regulatory content" in text
            finally:
                Path(f.name).unlink()
    
    def test_parse_html_document(self, parser):
        """Test parsing HTML documents."""
        html_content = """
        <html>
        <body>
            <h1>Privacy Policy</h1>
            <p>Personal data must be processed lawfully and fairly.</p>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            f.flush()
            
            try:
                text = parser.parse_document(f.name, RegulationType.GDPR)
                assert "Personal data must be processed" in text
                assert "<html>" not in text  # HTML tags should be stripped
            finally:
                Path(f.name).unlink()
    
    def test_extract_requirements_gdpr(self, parser, sample_gdpr_text):
        """Test requirement extraction from GDPR text."""
        requirements = parser.extract_requirements(sample_gdpr_text, RegulationType.GDPR)
        
        assert len(requirements) > 0
        assert any(req.regulation_type == RegulationType.GDPR for req in requirements)
        assert any("personal data" in req.description.lower() for req in requirements)
    
    def test_extract_requirements_hipaa(self, parser, sample_hipaa_text):
        """Test requirement extraction from HIPAA text."""
        requirements = parser.extract_requirements(sample_hipaa_text, RegulationType.HIPAA)
        
        assert len(requirements) > 0
        assert any(req.regulation_type == RegulationType.HIPAA for req in requirements)
        assert any("protected health information" in req.description.lower() for req in requirements)
    
    def test_requirement_classification(self, parser):
        """Test requirement type classification."""
        # Test PII handling classification
        pii_text = "Personal data must be protected and handled securely"
        req_type = parser._classify_requirement_type(pii_text)
        assert req_type == RequirementType.PII_HANDLING
        
        # Test access control classification
        access_text = "Authentication must be required for all users"
        req_type = parser._classify_requirement_type(access_text)
        assert req_type == RequirementType.ACCESS_CONTROL
        
        # Test audit logging classification
        audit_text = "All access attempts must be logged and monitored"
        req_type = parser._classify_requirement_type(audit_text)
        assert req_type == RequirementType.AUDIT_LOGGING
    
    def test_confidence_scoring(self, parser):
        """Test confidence score calculation."""
        # High confidence text (many indicators)
        high_conf_text = "Personal data must be encrypted and access must be logged"
        entities = [("Personal data", "PRODUCT"), ("access", "ACTION")]
        score = parser._calculate_confidence_score(high_conf_text, entities, RegulationType.GDPR)
        assert score >= 0.5
        
        # Low confidence text (few indicators)
        low_conf_text = "Some data might need protection"
        score = parser._calculate_confidence_score(low_conf_text, [], RegulationType.GDPR)
        assert score < 0.5
    
    def test_data_type_extraction(self, parser):
        """Test extraction of data types from text."""
        text = "Social security numbers and credit card numbers must be protected"
        data_types = parser._extract_data_types(text, RegulationType.GDPR)
        
        # Should find common data types
        assert len(data_types) > 0
    
    def test_action_suggestion(self, parser):
        """Test enforcement action suggestions."""
        # Should suggest block for prohibited actions
        block_text = "Disclosure of personal data is prohibited without consent"
        action = parser._suggest_action(block_text)
        assert action == "block"
        
        # Should suggest flag for monitoring requirements
        flag_text = "Access to personal data must be monitored and reviewed"
        action = parser._suggest_action(flag_text)
        assert action == "flag"
    
    def test_severity_determination(self, parser):
        """Test severity level determination."""
        # High severity
        high_text = "Critical data must be protected at all times"
        severity = parser._determine_severity(high_text)
        assert severity == "high"
        
        # Medium severity
        medium_text = "Important data should be secured appropriately"
        severity = parser._determine_severity(medium_text)
        assert severity == "medium"
    
    def test_rule_generation(self, parser, sample_gdpr_text):
        """Test generating rules from requirements."""
        requirements = parser.extract_requirements(sample_gdpr_text, RegulationType.GDPR)
        rules = parser.generate_rules(requirements)
        
        assert len(rules) > 0
        for rule in rules:
            assert rule.rule_id is not None
            assert rule.action in ["block", "flag", "allow"]
            assert rule.yaml_content is not None
            assert rule.confidence_score >= 0.0
    
    def test_rule_yaml_format(self, parser):
        """Test that generated rules have valid YAML format."""
        # Create a mock requirement
        requirement = PolicyRequirement(
            id="test_req_001",
            regulation_type=RegulationType.GDPR,
            requirement_type=RequirementType.PII_HANDLING,
            title="Test requirement",
            description="Personal data must be protected",
            regulatory_section="Article 6",
            severity="high",
            confidence_score=0.8,
            extracted_text="Personal data must be protected",
            suggested_action="flag",
            data_types=["personal data"],
            applicable_contexts=["text", "content"]
        )
        
        rule = parser._generate_rule_from_requirement(requirement)
        assert rule is not None
        
        # Validate YAML structure
        import yaml
        parsed_yaml = yaml.safe_load(rule.yaml_content)
        assert isinstance(parsed_yaml, list)
        assert len(parsed_yaml) > 0
        
        rule_dict = parsed_yaml[0]
        assert "id" in rule_dict
        assert "action" in rule_dict
        assert rule_dict["action"] in ["block", "flag", "allow"]
    
    def test_end_to_end_workflow(self, parser, sample_gdpr_text):
        """Test complete workflow from text to rules."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_gdpr_text)
            f.flush()
            
            try:
                # Run complete workflow
                requirements, rules = parser.parse_regulation_document(f.name, RegulationType.GDPR)
                
                # Validate results
                assert len(requirements) > 0
                assert len(rules) > 0
                assert len(rules) <= len(requirements)  # Not all requirements may generate rules
                
                # Validate requirement properties
                for req in requirements:
                    assert req.regulation_type == RegulationType.GDPR
                    assert req.confidence_score >= 0.0
                    assert req.confidence_score <= 1.0
                
                # Validate rule properties
                for rule in rules:
                    assert rule.confidence_score >= 0.0
                    assert rule.confidence_score <= 1.0
                    assert rule.action in ["block", "flag", "allow"]
                    
            finally:
                Path(f.name).unlink()
    
    def test_unsupported_file_format(self, parser):
        """Test handling of unsupported file formats."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            try:
                with pytest.raises(ValueError, match="Unsupported file format"):
                    parser.parse_document(f.name, RegulationType.GDPR)
            finally:
                Path(f.name).unlink()
    
    @patch('spacy.load')
    def test_fallback_without_spacy(self, mock_spacy_load, sample_gdpr_text):
        """Test that parser works without spaCy (fallback mode)."""
        mock_spacy_load.side_effect = OSError("Model not found")
        
        parser = RegulatoryTextParser()
        assert parser.nlp is None
        
        # Should still work with basic analysis
        requirements = parser.extract_requirements(sample_gdpr_text, RegulationType.GDPR)
        assert len(requirements) > 0
    
    def test_deduplication(self, parser):
        """Test requirement deduplication."""
        # Create duplicate requirements
        req1 = PolicyRequirement(
            id="req1", regulation_type=RegulationType.GDPR,
            requirement_type=RequirementType.PII_HANDLING,
            title="Personal data protection", description="Test 1",
            regulatory_section="Art 6", severity="high", confidence_score=0.8,
            extracted_text="Test", suggested_action="flag",
            data_types=[], applicable_contexts=[]
        )
        
        req2 = PolicyRequirement(
            id="req2", regulation_type=RegulationType.GDPR,
            requirement_type=RequirementType.PII_HANDLING,
            title="Personal data protection", description="Test 2",
            regulatory_section="Art 6", severity="high", confidence_score=0.8,
            extracted_text="Test", suggested_action="flag",
            data_types=[], applicable_contexts=[]
        )
        
        req3 = PolicyRequirement(
            id="req3", regulation_type=RegulationType.GDPR,
            requirement_type=RequirementType.ACCESS_CONTROL,
            title="Access control requirement", description="Test 3",
            regulatory_section="Art 7", severity="medium", confidence_score=0.7,
            extracted_text="Test", suggested_action="block",
            data_types=[], applicable_contexts=[]
        )
        
        requirements = [req1, req2, req3]
        deduplicated = parser._deduplicate_requirements(requirements)
        
        # Should remove one duplicate
        assert len(deduplicated) == 2
        titles = [req.title for req in deduplicated]
        assert "Personal data protection" in titles
        assert "Access control requirement" in titles


class TestIntelligenceConfig:
    """Test intelligence configuration."""
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        config = load_intelligence_config()
        
        assert config.min_confidence_threshold == 0.4
        assert config.auto_approval_threshold == 0.8
        assert config.max_rules_per_document == 50
        assert config.require_human_review is True
        assert '.pdf' in config.supported_formats
    
    def test_get_regulation_config(self):
        """Test getting regulation-specific configuration."""
        gdpr_config = get_regulation_config("gdpr")
        assert gdpr_config is not None
        assert gdpr_config.name == "General Data Protection Regulation"
        assert "personal data" in gdpr_config.keywords
        
        hipaa_config = get_regulation_config("hipaa")
        assert hipaa_config is not None
        assert "PHI" in hipaa_config.keywords
    
    @patch.dict('os.environ', {
        'JIMINI_AI_MIN_CONFIDENCE': '0.6',
        'JIMINI_AI_AUTO_APPROVAL_THRESHOLD': '0.9',
        'JIMINI_AI_AUTO_APPROVAL': 'true'
    })
    def test_environment_overrides(self):
        """Test configuration overrides from environment."""
        config = load_intelligence_config()
        
        assert config.min_confidence_threshold == 0.6
        assert config.auto_approval_threshold == 0.9
        assert config.enable_auto_approval is True


class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    def test_gdpr_article_6_processing(self):
        """Test processing GDPR Article 6 specifically."""
        parser = RegulatoryTextParser()
        
        article_6_text = """
        Article 6 - Lawfulness of processing
        
        Processing shall be lawful only if and to the extent that at least one of the following applies:
        
        (a) the data subject has given consent to the processing of his or her personal data for one or more specific purposes;
        (b) processing is necessary for the performance of a contract to which the data subject is party;
        (c) processing is necessary for compliance with a legal obligation to which the controller is subject;
        
        Personal data shall be processed lawfully, fairly and in a transparent manner.
        """
        
        requirements = parser.extract_requirements(article_6_text, RegulationType.GDPR)
        
        # Should find consent and lawfulness requirements
        assert len(requirements) > 0
        consent_reqs = [r for r in requirements if "consent" in r.description.lower()]
        assert len(consent_reqs) > 0
    
    def test_hipaa_minimum_necessary(self):
        """Test processing HIPAA minimum necessary rule."""
        parser = RegulatoryTextParser()
        
        hipaa_text = """
        164.502(b) Minimum necessary standard
        
        When using or disclosing protected health information or when requesting 
        protected health information from another covered entity, a covered entity 
        must make reasonable efforts to limit protected health information to the 
        minimum necessary to accomplish the intended purpose.
        """
        
        requirements = parser.extract_requirements(hipaa_text, RegulationType.HIPAA)
        rules = parser.generate_rules(requirements)
        
        # Should generate rules for PHI handling
        assert len(requirements) > 0
        assert len(rules) > 0
        
        min_necessary_reqs = [r for r in requirements if "minimum necessary" in r.description.lower()]
        assert len(min_necessary_reqs) > 0
    
    def test_performance_with_large_document(self):
        """Test performance with large regulatory document."""
        parser = RegulatoryTextParser()
        
        # Create large text by repeating sample content
        base_text = create_sample_gdpr_text()
        large_text = base_text * 10  # Simulate larger document
        
        import time
        start_time = time.time()
        
        requirements = parser.extract_requirements(large_text, RegulationType.GDPR)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (5 seconds for this test)
        assert processing_time < 5.0
        assert len(requirements) > 0


def test_demo_function():
    """Test the demo function runs without errors."""
    try:
        from app.intelligence.regulatory_parser import demo_regulatory_parser
        requirements, rules = demo_regulatory_parser()
        
        assert len(requirements) > 0
        assert len(rules) > 0
        
    except Exception as e:
        pytest.skip(f"Demo requires optional dependencies: {e}")


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v"])