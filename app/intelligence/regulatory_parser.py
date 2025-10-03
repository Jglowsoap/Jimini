"""
Phase 6A - Regulatory Text Parser Prototype
AI-powered conversion of regulatory documents to executable policy rules

This module demonstrates the intelligence expansion capability by:
1. Parsing regulatory documents (PDF/HTML/text)
2. Extracting policy requirements using NLP
3. Generating YAML rules with confidence scores
4. Providing approval workflow for AI-generated rules
"""

import re
import json
import spacy
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import yaml
from datetime import datetime
import PyPDF2
from bs4 import BeautifulSoup
import requests

# Import transformers for advanced NLP
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class RegulationType(str, Enum):
    """Supported regulation types."""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOX = "sox"
    CCPA = "ccpa"
    CJIS = "cjis"
    CUSTOM = "custom"


class RequirementType(str, Enum):
    """Types of policy requirements."""
    DATA_PROTECTION = "data_protection"
    ACCESS_CONTROL = "access_control"
    AUDIT_LOGGING = "audit_logging"
    ENCRYPTION = "encryption"
    PII_HANDLING = "pii_handling"
    RETENTION = "retention"
    DISCLOSURE = "disclosure"
    CONSENT = "consent"


@dataclass
class PolicyRequirement:
    """Extracted policy requirement from regulatory text."""
    id: str
    regulation_type: RegulationType
    requirement_type: RequirementType
    title: str
    description: str
    regulatory_section: str
    severity: str  # "high", "medium", "low"
    confidence_score: float  # 0.0 to 1.0
    extracted_text: str
    suggested_action: str
    data_types: List[str]
    applicable_contexts: List[str]


@dataclass
class GeneratedRule:
    """AI-generated policy rule."""
    rule_id: str
    name: str
    description: str
    pattern: Optional[str]
    llm_prompt: Optional[str]
    action: str  # "block", "flag", "allow"
    confidence_score: float
    source_requirement: PolicyRequirement
    applies_to: List[str]
    endpoints: List[str]
    yaml_content: str
    requires_approval: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class RegulatoryTextParser:
    """
    Main class for parsing regulatory documents and generating policy rules.
    
    Features:
    - Multiple document format support (PDF, HTML, text)
    - NLP-powered requirement extraction
    - Template-based rule generation
    - Confidence scoring and approval workflow
    """
    
    def __init__(self):
        self.nlp = self._load_spacy_model()
        self.classifier = self._load_classification_model()
        self.rule_templates = self._load_rule_templates()
        self.regulation_patterns = self._load_regulation_patterns()
        
    def _load_spacy_model(self):
        """Load spaCy NLP model."""
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            return None
    
    def _load_classification_model(self):
        """Load transformer model for requirement classification."""
        if not HAS_TRANSFORMERS:
            print("Warning: transformers not available. Install with: pip install transformers")
            return None
            
        try:
            # Use a pre-trained model for text classification
            return pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                tokenizer="microsoft/DialoGPT-medium"
            )
        except Exception as e:
            print(f"Warning: Could not load transformer model: {e}")
            return None
    
    def _load_rule_templates(self) -> Dict[RequirementType, Dict[str, Any]]:
        """Load rule templates for different requirement types."""
        return {
            RequirementType.PII_HANDLING: {
                "pattern_template": r"\b(?:SSN|social security|credit card|{data_type})\b",
                "action": "block",
                "description_template": "Detect and block {data_type} in content",
                "applies_to": ["text", "content"]
            },
            RequirementType.DATA_PROTECTION: {
                "llm_prompt_template": "Evaluate if the text contains sensitive data that should be protected under {regulation}",
                "action": "flag",
                "description_template": "Flag content for {regulation} compliance review",
                "applies_to": ["text", "content", "data"]
            },
            RequirementType.ACCESS_CONTROL: {
                "pattern_template": r"\b(?:password|token|key|secret|{access_type})\b",
                "action": "block",
                "description_template": "Block exposure of {access_type} credentials",
                "applies_to": ["text", "content", "credentials"]
            },
            RequirementType.AUDIT_LOGGING: {
                "action": "flag",
                "description_template": "Ensure audit logging for {activity_type} under {regulation}",
                "applies_to": ["audit", "logging", "compliance"]
            }
        }
    
    def _load_regulation_patterns(self) -> Dict[RegulationType, Dict[str, Any]]:
        """Load patterns specific to different regulations."""
        return {
            RegulationType.GDPR: {
                "keywords": ["personal data", "data subject", "processing", "consent", "lawful basis"],
                "data_types": ["name", "email", "phone", "address", "ip address", "cookies"],
                "sections": ["Article 6", "Article 7", "Article 17", "Article 20"]
            },
            RegulationType.HIPAA: {
                "keywords": ["PHI", "protected health information", "medical record", "treatment"],
                "data_types": ["medical record number", "social security number", "health plan number"],
                "sections": ["164.502", "164.506", "164.508", "164.512"]
            },
            RegulationType.PCI_DSS: {
                "keywords": ["cardholder data", "payment card", "credit card", "sensitive authentication"],
                "data_types": ["credit card number", "CVV", "PIN", "magnetic stripe"],
                "sections": ["Requirement 3", "Requirement 4", "Requirement 7", "Requirement 8"]
            }
        }
    
    def parse_document(self, file_path: str, regulation_type: RegulationType) -> str:
        """Parse document and extract text content."""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            return self._parse_pdf(file_path)
        elif file_path.suffix.lower() in ['.html', '.htm']:
            return self._parse_html(file_path)
        elif file_path.suffix.lower() == '.txt':
            return self._parse_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    def _parse_pdf(self, file_path: Path) -> str:
        """Extract text from PDF document."""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {e}")
    
    def _parse_html(self, file_path: Path) -> str:
        """Extract text from HTML document."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                return soup.get_text(separator=' ', strip=True)
        except Exception as e:
            raise ValueError(f"Failed to parse HTML: {e}")
    
    def _parse_text(self, file_path: Path) -> str:
        """Read plain text document."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise ValueError(f"Failed to parse text file: {e}")
    
    def extract_requirements(self, text: str, regulation_type: RegulationType) -> List[PolicyRequirement]:
        """Extract policy requirements from regulatory text using NLP."""
        requirements = []
        
        # Split text into sections/paragraphs
        sections = self._split_into_sections(text, regulation_type)
        
        for section_num, section_text in enumerate(sections):
            # Analyze each section for policy requirements
            section_requirements = self._analyze_section(section_text, section_num, regulation_type)
            requirements.extend(section_requirements)
        
        # Remove duplicates and merge similar requirements
        return self._deduplicate_requirements(requirements)
    
    def _split_into_sections(self, text: str, regulation_type: RegulationType) -> List[str]:
        """Split text into logical sections based on regulation structure."""
        patterns = self.regulation_patterns.get(regulation_type, {})
        sections = patterns.get("sections", [])
        
        # Try to split by known section patterns
        if sections:
            # Look for section headers in the text
            section_pattern = "|".join(re.escape(section) for section in sections)
            parts = re.split(f"({section_pattern})", text, flags=re.IGNORECASE)
        else:
            # Fallback: split by paragraphs
            parts = text.split('\n\n')
        
        # Filter out empty sections
        return [part.strip() for part in parts if part.strip() and len(part.strip()) > 50]
    
    def _analyze_section(self, section_text: str, section_num: int, regulation_type: RegulationType) -> List[PolicyRequirement]:
        """Analyze a text section for policy requirements."""
        requirements = []
        
        if not self.nlp:
            return self._analyze_section_basic(section_text, section_num, regulation_type)
        
        # Process with spaCy NLP
        doc = self.nlp(section_text)
        
        # Extract entities and key phrases
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        # Look for requirement indicators
        requirement_indicators = [
            "must", "shall", "should", "required", "mandatory", "obligated",
            "prohibited", "forbidden", "not permitted", "ensure", "implement"
        ]
        
        sentences = [sent.text for sent in doc.sents]
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            
            # Check if sentence contains requirement indicators
            if any(indicator in sentence_lower for indicator in requirement_indicators):
                requirement = self._create_requirement_from_sentence(
                    sentence, entities, section_num, i, regulation_type
                )
                if requirement:
                    requirements.append(requirement)
        
        return requirements
    
    def _analyze_section_basic(self, section_text: str, section_num: int, regulation_type: RegulationType) -> List[PolicyRequirement]:
        """Basic analysis without advanced NLP."""
        requirements = []
        
        # Simple pattern-based extraction
        requirement_patterns = [
            r"(must|shall|required to|obligated to)\s+(.+?)(?:\.|$)",
            r"(prohibited|forbidden|not permitted)\s+(.+?)(?:\.|$)",
            r"(personal data|sensitive data|confidential information)\s+(.+?)(?:\.|$)"
        ]
        
        for pattern in requirement_patterns:
            matches = re.finditer(pattern, section_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                requirement_text = match.group(0)
                requirement = PolicyRequirement(
                    id=f"req_{regulation_type.value}_{section_num}_{len(requirements)}",
                    regulation_type=regulation_type,
                    requirement_type=self._classify_requirement_type(requirement_text),
                    title=requirement_text[:100] + "..." if len(requirement_text) > 100 else requirement_text,
                    description=requirement_text,
                    regulatory_section=f"Section {section_num}",
                    severity="medium",
                    confidence_score=0.6,  # Lower confidence for basic analysis
                    extracted_text=requirement_text,
                    suggested_action=self._suggest_action(requirement_text),
                    data_types=self._extract_data_types(requirement_text, regulation_type),
                    applicable_contexts=["text", "content"]
                )
                requirements.append(requirement)
        
        return requirements
    
    def _create_requirement_from_sentence(self, sentence: str, entities: List[Tuple[str, str]], 
                                        section_num: int, sentence_num: int, 
                                        regulation_type: RegulationType) -> Optional[PolicyRequirement]:
        """Create a policy requirement from an analyzed sentence."""
        
        # Classify requirement type
        req_type = self._classify_requirement_type(sentence)
        
        # Calculate confidence score
        confidence = self._calculate_confidence_score(sentence, entities, regulation_type)
        
        # Skip low-confidence requirements
        if confidence < 0.4:
            return None
        
        # Extract data types mentioned
        data_types = self._extract_data_types(sentence, regulation_type)
        
        # Suggest enforcement action
        suggested_action = self._suggest_action(sentence)
        
        return PolicyRequirement(
            id=f"req_{regulation_type.value}_{section_num}_{sentence_num}",
            regulation_type=regulation_type,
            requirement_type=req_type,
            title=sentence[:100] + "..." if len(sentence) > 100 else sentence,
            description=sentence,
            regulatory_section=f"Section {section_num}",
            severity=self._determine_severity(sentence),
            confidence_score=confidence,
            extracted_text=sentence,
            suggested_action=suggested_action,
            data_types=data_types,
            applicable_contexts=self._determine_contexts(sentence, req_type)
        )
    
    def _classify_requirement_type(self, text: str) -> RequirementType:
        """Classify the type of policy requirement."""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["personal data", "pii", "sensitive data"]):
            return RequirementType.PII_HANDLING
        elif any(term in text_lower for term in ["access", "authentication", "authorization"]):
            return RequirementType.ACCESS_CONTROL
        elif any(term in text_lower for term in ["log", "audit", "record", "monitoring"]):
            return RequirementType.AUDIT_LOGGING
        elif any(term in text_lower for term in ["encrypt", "cryptograph", "secure transmission"]):
            return RequirementType.ENCRYPTION
        elif any(term in text_lower for term in ["retention", "delete", "storage", "archival"]):
            return RequirementType.RETENTION
        elif any(term in text_lower for term in ["disclose", "share", "transfer"]):
            return RequirementType.DISCLOSURE
        elif any(term in text_lower for term in ["consent", "permission", "opt-in"]):
            return RequirementType.CONSENT
        else:
            return RequirementType.DATA_PROTECTION
    
    def _calculate_confidence_score(self, sentence: str, entities: List[Tuple[str, str]], 
                                  regulation_type: RegulationType) -> float:
        """Calculate confidence score for requirement extraction."""
        score = 0.0
        
        # Base score for requirement indicators
        requirement_indicators = ["must", "shall", "required", "mandatory", "prohibited"]
        if any(indicator in sentence.lower() for indicator in requirement_indicators):
            score += 0.3
        
        # Bonus for relevant entities
        relevant_entities = ["ORG", "PERSON", "GPE", "PRODUCT"]
        entity_labels = [label for _, label in entities]
        if any(label in relevant_entities for label in entity_labels):
            score += 0.2
        
        # Bonus for regulation-specific keywords
        patterns = self.regulation_patterns.get(regulation_type, {})
        keywords = patterns.get("keywords", [])
        if any(keyword in sentence.lower() for keyword in keywords):
            score += 0.3
        
        # Bonus for data types
        data_types = patterns.get("data_types", [])
        if any(data_type in sentence.lower() for data_type in data_types):
            score += 0.2
        
        return min(1.0, score)
    
    def _extract_data_types(self, text: str, regulation_type: RegulationType) -> List[str]:
        """Extract data types mentioned in the text."""
        patterns = self.regulation_patterns.get(regulation_type, {})
        data_types = patterns.get("data_types", [])
        
        found_types = []
        text_lower = text.lower()
        
        for data_type in data_types:
            if data_type.lower() in text_lower:
                found_types.append(data_type)
        
        # Generic data type patterns
        generic_patterns = [
            r"\b(?:social security number|ssn)\b",
            r"\b(?:credit card number|payment card)\b",
            r"\b(?:email address|email)\b",
            r"\b(?:phone number|telephone)\b",
            r"\b(?:ip address|ip)\b"
        ]
        
        for pattern in generic_patterns:
            matches = re.findall(pattern, text_lower)
            found_types.extend(matches)
        
        return list(set(found_types))  # Remove duplicates
    
    def _suggest_action(self, text: str) -> str:
        """Suggest enforcement action based on requirement text."""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["prohibited", "forbidden", "must not", "shall not"]):
            return "block"
        elif any(term in text_lower for term in ["review", "monitor", "audit", "check"]):
            return "flag"
        else:
            return "flag"  # Default to flag for review
    
    def _determine_severity(self, text: str) -> str:
        """Determine severity level of the requirement."""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["critical", "essential", "vital", "mandatory"]):
            return "high"
        elif any(term in text_lower for term in ["important", "significant", "required"]):
            return "medium"
        else:
            return "low"
    
    def _determine_contexts(self, text: str, req_type: RequirementType) -> List[str]:
        """Determine applicable contexts for the requirement."""
        contexts = ["text", "content"]
        
        if req_type == RequirementType.ACCESS_CONTROL:
            contexts.extend(["authentication", "authorization"])
        elif req_type == RequirementType.AUDIT_LOGGING:
            contexts.extend(["logging", "monitoring"])
        elif req_type == RequirementType.ENCRYPTION:
            contexts.extend(["transmission", "storage"])
        
        return contexts
    
    def _deduplicate_requirements(self, requirements: List[PolicyRequirement]) -> List[PolicyRequirement]:
        """Remove duplicate and merge similar requirements."""
        # Simple deduplication by title similarity
        unique_requirements = []
        seen_titles = set()
        
        for req in requirements:
            title_key = req.title.lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_requirements.append(req)
        
        return unique_requirements
    
    def generate_rules(self, requirements: List[PolicyRequirement]) -> List[GeneratedRule]:
        """Generate YAML policy rules from extracted requirements."""
        generated_rules = []
        
        for req in requirements:
            rule = self._generate_rule_from_requirement(req)
            if rule:
                generated_rules.append(rule)
        
        return generated_rules
    
    def _generate_rule_from_requirement(self, requirement: PolicyRequirement) -> Optional[GeneratedRule]:
        """Generate a single rule from a policy requirement."""
        template = self.rule_templates.get(requirement.requirement_type)
        if not template:
            return None
        
        # Generate rule ID
        rule_id = f"{requirement.regulation_type.value.upper()}-{requirement.requirement_type.value.upper()}-{requirement.id[-3:]}"
        
        # Create rule content based on template
        rule_content = {
            "id": rule_id,
            "name": f"{requirement.regulation_type.value.upper()} - {requirement.title[:50]}",
            "description": requirement.description,
            "action": template["action"],
            "applies_to": template["applies_to"],
            "endpoints": ["*"]  # Default to all endpoints
        }
        
        # Add pattern or LLM prompt based on template
        if "pattern_template" in template:
            # Generate regex pattern
            pattern = template["pattern_template"]
            for data_type in requirement.data_types:
                pattern = pattern.replace("{data_type}", data_type)
            rule_content["pattern"] = pattern
        elif "llm_prompt_template" in template:
            # Generate LLM prompt
            prompt = template["llm_prompt_template"]
            prompt = prompt.replace("{regulation}", requirement.regulation_type.value.upper())
            rule_content["llm_prompt"] = prompt
        
        # Convert to YAML
        yaml_content = yaml.dump([rule_content], default_flow_style=False, sort_keys=False)
        
        return GeneratedRule(
            rule_id=rule_id,
            name=rule_content["name"],
            description=rule_content["description"],
            pattern=rule_content.get("pattern"),
            llm_prompt=rule_content.get("llm_prompt"),
            action=rule_content["action"],
            confidence_score=requirement.confidence_score,
            source_requirement=requirement,
            applies_to=rule_content["applies_to"],
            endpoints=rule_content["endpoints"],
            yaml_content=yaml_content,
            requires_approval=requirement.confidence_score < 0.8  # High confidence rules auto-approve
        )
    
    def parse_regulation_document(self, file_path: str, regulation_type: RegulationType) -> Tuple[List[PolicyRequirement], List[GeneratedRule]]:
        """Complete workflow: parse document and generate rules."""
        # Parse document
        text = self.parse_document(file_path, regulation_type)
        
        # Extract requirements
        requirements = self.extract_requirements(text, regulation_type)
        
        # Generate rules
        rules = self.generate_rules(requirements)
        
        return requirements, rules


# Example usage and test functions
def create_sample_gdpr_text() -> str:
    """Create sample GDPR text for testing."""
    return """
    Article 6 - Lawfulness of processing
    
    1. Processing shall be lawful only if and to the extent that at least one of the following applies:
    
    (a) the data subject has given consent to the processing of his or her personal data for one or more specific purposes;
    (b) processing is necessary for the performance of a contract to which the data subject is party;
    (c) processing is necessary for compliance with a legal obligation to which the controller is subject;
    
    Article 17 - Right to erasure ('right to be forgotten')
    
    1. The data subject shall have the right to obtain from the controller the erasure of personal data concerning him or her without undue delay and the controller shall have the obligation to erase personal data without undue delay where one of the following grounds applies:
    
    (a) the personal data are no longer necessary in relation to the purposes for which they were collected or otherwise processed;
    (b) the data subject withdraws consent on which the processing is based according to point (a) of Article 6(1)
    
    Personal data must be processed lawfully, fairly and in a transparent manner in relation to the data subject.
    
    Controllers must implement appropriate technical and organizational measures to ensure a level of security appropriate to the risk.
    
    Any processing of personal data must have a lawful basis as set out in Article 6.
    """


def demo_regulatory_parser():
    """Demonstrate the regulatory text parser."""
    print("🧠 Phase 6A - Regulatory Text Parser Demo")
    print("=" * 50)
    
    # Initialize parser
    parser = RegulatoryTextParser()
    
    # Create sample text
    gdpr_text = create_sample_gdpr_text()
    
    print("📄 Sample GDPR Text:")
    print(gdpr_text[:200] + "...")
    print()
    
    # Extract requirements
    print("🔍 Extracting Policy Requirements...")
    requirements = parser.extract_requirements(gdpr_text, RegulationType.GDPR)
    
    print(f"✅ Found {len(requirements)} policy requirements:")
    for i, req in enumerate(requirements[:3], 1):  # Show first 3
        print(f"  {i}. {req.title}")
        print(f"     Type: {req.requirement_type.value}")
        print(f"     Confidence: {req.confidence_score:.2f}")
        print(f"     Action: {req.suggested_action}")
        print()
    
    # Generate rules
    print("⚙️ Generating Policy Rules...")
    rules = parser.generate_rules(requirements)
    
    print(f"✅ Generated {len(rules)} policy rules:")
    for i, rule in enumerate(rules[:2], 1):  # Show first 2
        print(f"  {i}. {rule.name}")
        print(f"     ID: {rule.rule_id}")
        print(f"     Action: {rule.action}")
        print(f"     Confidence: {rule.confidence_score:.2f}")
        print(f"     Requires Approval: {rule.requires_approval}")
        print("     YAML Preview:")
        print("     " + "\n     ".join(rule.yaml_content.split('\n')[:5]))
        print()
    
    print("🎯 Demo completed! This showcases Phase 6A intelligence expansion.")
    return requirements, rules


if __name__ == "__main__":
    # Run demo
    demo_regulatory_parser()