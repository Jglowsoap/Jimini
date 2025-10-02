#!/usr/bin/env python3
"""
Phase 6A Intelligence Demo Script
Demonstrates AI-powered regulatory analysis capabilities
"""

import os
import sys
import tempfile
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_sample_documents():
    """Create sample regulatory documents for demonstration."""
    
    # Sample GDPR Article 6
    gdpr_content = """
    CHAPTER II - PRINCIPLES
    
    Article 6 - Lawfulness of processing
    
    1. Processing shall be lawful only if and to the extent that at least one of the following applies:
    
    (a) the data subject has given consent to the processing of his or her personal data for one or more specific purposes;
    (b) processing is necessary for the performance of a contract to which the data subject is party or in order to take steps at the request of the data subject prior to entering into a contract;
    (c) processing is necessary for compliance with a legal obligation to which the controller is subject;
    (d) processing is necessary in order to protect the vital interests of the data subject or of another natural person;
    (e) processing is necessary for the performance of a task carried out in the public interest or in the exercise of official authority vested in the controller;
    (f) processing is necessary for the purposes of the legitimate interests pursued by the controller or by a third party, except where such interests are overridden by the interests or fundamental rights and freedoms of the data subject which require protection of personal data, in particular where the data subject is a child.
    
    2. Point (f) of paragraph 1 shall not apply to processing carried out by public authorities in the performance of their tasks.
    
    Article 7 - Conditions for consent
    
    1. Where processing is based on consent, the controller shall be able to demonstrate that the data subject has consented to processing of his or her personal data.
    
    2. If the data subject's consent is given in the context of a written declaration which also concerns other matters, the request for consent shall be presented in a manner which is clearly distinguishable from the other matters, in an intelligible and easily accessible form, using clear and plain language. Any part of such a declaration which constitutes an infringement of this Regulation shall not be binding.
    
    3. The data subject shall have the right to withdraw his or her consent at any time. The withdrawal of consent shall not affect the lawfulness of processing based on consent before its withdrawal. Prior to giving consent, the data subject shall be informed of his or her right to withdraw consent. It shall be as easy to withdraw consent as to give consent.
    
    4. When assessing whether consent is freely given, utmost account shall be taken of whether, inter alia, the performance of a contract, including the provision of a service, is conditional on consent to the processing of personal data that is not necessary for the performance of that contract.
    """
    
    # Sample HIPAA Privacy Rule
    hipaa_content = """
    PART 164 - SECURITY AND PRIVACY
    
    Subpart E - Privacy of Individually Identifiable Health Information
    
    § 164.502 Uses and disclosures of protected health information: General rules.
    
    (a) Standard: A covered entity may not use or disclose protected health information, except as permitted or required by this subpart or by subpart C of part 160 of this subchapter.
    
    (b) Standard: Minimum necessary. When using or disclosing protected health information or when requesting protected health information from another covered entity, a covered entity must make reasonable efforts to limit protected health information to the minimum necessary to accomplish the intended purpose of the use, disclosure, or request.
    
    § 164.506 Uses and disclosures to carry out treatment, payment, or health care operations.
    
    (a) Standard: A covered entity may use or disclose protected health information for its own treatment, payment, or health care operations activities, as described in paragraph (c) of this section.
    
    (b) Standard: A covered entity may disclose protected health information for treatment activities of a health care provider.
    
    § 164.508 Uses and disclosures for which an authorization is required.
    
    (a) Standard: Authorizations required. Except as otherwise permitted or required by this subchapter, a covered entity may use or disclose protected health information only with the valid authorization of the individual who is the subject of the information.
    
    (b) Standard: Authorization required: Psychotherapy notes. Notwithstanding any provision of this subpart, other than the transition provisions in § 164.532, a covered entity must obtain an authorization for any use or disclosure of psychotherapy notes, except:
    
    (1) To carry out the following treatment, payment, or health care operations:
        (i) Use by the originator of the psychotherapy notes for treatment;
        (ii) Use or disclosure by the covered entity for its own training programs in which students, trainees, or practitioners in mental health learn under supervision to practice or improve their skills in group, joint, family, or individual counseling; or
        (iii) Use or disclosure by the covered entity to defend itself in a legal action or other proceeding brought by the individual;
    """
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as gdpr_file:
        gdpr_file.write(gdpr_content)
        gdpr_file.flush()
        gdpr_path = gdpr_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as hipaa_file:
        hipaa_file.write(hipaa_content)
        hipaa_file.flush()
        hipaa_path = hipaa_file.name
    
    return gdpr_path, hipaa_path


def demo_intelligence_system():
    """Run comprehensive intelligence system demonstration."""
    print("🧠 Jimini Phase 6A - Intelligence Expansion Demo")
    print("=" * 60)
    print()
    
    try:
        from app.intelligence.regulatory_parser import RegulatoryTextParser, RegulationType
        from app.intelligence.config import validate_intelligence_setup, load_intelligence_config
        
        # Check system setup
        print("🔧 Checking Intelligence System Setup...")
        setup_status = validate_intelligence_setup()
        
        print("Setup Status:")
        for component, available in setup_status.items():
            status_icon = "✅" if available else "❌"
            print(f"  {status_icon} {component.replace('_', ' ').title()}: {'Available' if available else 'Missing'}")
        
        if not setup_status.get('spacy_available', False):
            print("\n⚠️  spaCy not available. Install with: pip install spacy")
            print("   Then download model: python -m spacy download en_core_web_sm")
        
        print()
        
        # Load configuration
        print("⚙️ Loading Intelligence Configuration...")
        config = load_intelligence_config()
        print(f"  • Min Confidence Threshold: {config.min_confidence_threshold}")
        print(f"  • Auto Approval Threshold: {config.auto_approval_threshold}")
        print(f"  • Max Rules per Document: {config.max_rules_per_document}")
        print(f"  • Supported Formats: {', '.join(config.supported_formats)}")
        print()
        
        # Create sample documents
        print("📄 Creating Sample Regulatory Documents...")
        gdpr_path, hipaa_path = create_sample_documents()
        print(f"  • GDPR sample: {Path(gdpr_path).name}")
        print(f"  • HIPAA sample: {Path(hipaa_path).name}")
        print()
        
        # Initialize parser
        print("🚀 Initializing AI-Powered Regulatory Parser...")
        parser = RegulatoryTextParser()
        print("  ✅ Parser initialized successfully")
        print()
        
        # Demo 1: GDPR Analysis
        print("📊 Demo 1: GDPR Article 6 & 7 Analysis")
        print("-" * 40)
        
        try:
            requirements, rules = parser.parse_regulation_document(gdpr_path, RegulationType.GDPR)
            
            print(f"✅ Extracted {len(requirements)} policy requirements")
            print(f"✅ Generated {len(rules)} policy rules")
            print()
            
            # Show top requirements
            print("Top Policy Requirements:")
            for i, req in enumerate(requirements[:3], 1):
                print(f"  {i}. {req.title[:80]}{'...' if len(req.title) > 80 else ''}")
                print(f"     Type: {req.requirement_type.value}")
                print(f"     Confidence: {req.confidence_score:.2f}")
                print(f"     Action: {req.suggested_action}")
                print(f"     Data Types: {', '.join(req.data_types) if req.data_types else 'None detected'}")
                print()
            
            # Show generated rules
            print("Generated Policy Rules:")
            for i, rule in enumerate(rules[:2], 1):
                print(f"  {i}. Rule ID: {rule.rule_id}")
                print(f"     Name: {rule.name}")
                print(f"     Action: {rule.action}")
                print(f"     Confidence: {rule.confidence_score:.2f}")
                print(f"     Requires Approval: {'Yes' if rule.requires_approval else 'No'}")
                if rule.pattern:
                    print(f"     Pattern: {rule.pattern}")
                elif rule.llm_prompt:
                    print(f"     LLM Prompt: {rule.llm_prompt[:60]}...")
                print()
            
        except Exception as e:
            print(f"❌ GDPR analysis failed: {e}")
        
        # Demo 2: HIPAA Analysis
        print("📊 Demo 2: HIPAA Privacy Rule Analysis")
        print("-" * 40)
        
        try:
            requirements, rules = parser.parse_regulation_document(hipaa_path, RegulationType.HIPAA)
            
            print(f"✅ Extracted {len(requirements)} policy requirements")
            print(f"✅ Generated {len(rules)} policy rules")
            print()
            
            # Show HIPAA-specific insights
            phi_requirements = [req for req in requirements if "PHI" in req.description or "protected health information" in req.description.lower()]
            print(f"PHI-Related Requirements: {len(phi_requirements)}")
            
            for req in phi_requirements[:2]:
                print(f"  • {req.title[:70]}{'...' if len(req.title) > 70 else ''}")
                print(f"    Confidence: {req.confidence_score:.2f}")
            print()
            
        except Exception as e:
            print(f"❌ HIPAA analysis failed: {e}")
        
        # Demo 3: Rule Export
        print("📤 Demo 3: Rule Export & Integration")
        print("-" * 40)
        
        if rules:
            # Show YAML export sample
            sample_rule = rules[0]
            print("Sample Generated YAML Rule:")
            print("```yaml")
            print(sample_rule.yaml_content)
            print("```")
            print()
            
            # Show integration steps
            print("Integration Steps:")
            print("  1. Review generated rules in intelligence dashboard")
            print("  2. Approve high-confidence rules for deployment")
            print("  3. Export approved rules to policy_rules.yaml")
            print("  4. Rules automatically loaded into enforcement engine")
            print()
        
        # Demo 4: Performance Metrics
        print("📈 Demo 4: Performance & Capabilities")
        print("-" * 40)
        
        total_reqs = len(requirements) if 'requirements' in locals() else 0
        total_rules = len(rules) if 'rules' in locals() else 0
        
        print(f"Processing Statistics:")
        print(f"  • Total Requirements Extracted: {total_reqs}")
        print(f"  • Total Rules Generated: {total_rules}")
        print(f"  • Supported Regulations: {len(list(RegulationType))}")
        print(f"  • Document Formats: {len(config.supported_formats)}")
        
        high_conf_rules = [r for r in rules if r.confidence_score >= config.auto_approval_threshold] if 'rules' in locals() else []
        print(f"  • High Confidence Rules: {len(high_conf_rules)}")
        print()
        
        # Cleanup
        print("🧹 Cleaning up temporary files...")
        try:
            Path(gdpr_path).unlink()
            Path(hipaa_path).unlink()
            print("  ✅ Temporary files cleaned up")
        except Exception as e:
            print(f"  ⚠️  Cleanup warning: {e}")
        
        print()
        print("🎉 Intelligence System Demo Complete!")
        print()
        print("Next Steps:")
        print("  1. Install intelligence dependencies: pip install -r requirements-intelligence.txt")
        print("  2. Download spaCy model: python -m spacy download en_core_web_sm")
        print("  3. Start server with intelligence: jimini run-local --port 9000")
        print("  4. Access intelligence API: http://localhost:9000/v1/intelligence/")
        print("  5. Upload regulatory documents via POST /v1/intelligence/analyze-document")
        
    except ImportError as e:
        print(f"❌ Intelligence system not available: {e}")
        print()
        print("Installation Required:")
        print("  pip install spacy transformers PyPDF2 beautifulsoup4")
        print("  python -m spacy download en_core_web_sm")
        return False
    
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def demo_api_endpoints():
    """Demonstrate available API endpoints."""
    print("🌐 Intelligence API Endpoints")
    print("=" * 40)
    print()
    
    endpoints = [
        ("GET", "/v1/intelligence/status", "Get intelligence system status and capabilities"),
        ("POST", "/v1/intelligence/analyze-document", "Analyze regulatory document and generate rules"),
        ("GET", "/v1/intelligence/processing-jobs", "List all processing jobs"),
        ("GET", "/v1/intelligence/processing-jobs/{id}", "Get specific processing job details"),
        ("POST", "/v1/intelligence/approve-rule", "Approve a generated rule for deployment"),
        ("GET", "/v1/intelligence/approved-rules", "List all approved rules"),
        ("GET", "/v1/intelligence/export-rules/{id}", "Export generated rules as YAML"),
        ("DELETE", "/v1/intelligence/processing-jobs/{id}", "Delete a processing job"),
        ("POST", "/v1/intelligence/demo", "Run intelligence system demonstration"),
    ]
    
    for method, endpoint, description in endpoints:
        print(f"{method:6} {endpoint:45} - {description}")
    
    print()
    print("Example Usage:")
    print("""
    # Check system status
    curl http://localhost:9000/v1/intelligence/status
    
    # Analyze GDPR document
    curl -X POST http://localhost:9000/v1/intelligence/analyze-document \\
         -F "file=@gdpr_article_6.txt" \\
         -F "regulation_type=gdpr" \\
         -F "confidence_threshold=0.5"
    
    # List processing jobs
    curl http://localhost:9000/v1/intelligence/processing-jobs
    
    # Run demo
    curl -X POST http://localhost:9000/v1/intelligence/demo
    """)


if __name__ == "__main__":
    print("🧠 Jimini Intelligence Expansion - Phase 6A")
    print("AI-Powered Regulatory Analysis & Rule Generation")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--api-only":
        demo_api_endpoints()
    else:
        success = demo_intelligence_system()
        if success:
            print("\n" + "="*60)
            demo_api_endpoints()
        
        sys.exit(0 if success else 1)