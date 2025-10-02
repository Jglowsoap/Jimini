"""
Phase 6A - Intelligence Configuration
Configuration management for AI-powered regulatory analysis
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class AIModel(str, Enum):
    """Supported AI models for different tasks."""
    SPACY_SM = "en_core_web_sm"
    SPACY_LG = "en_core_web_lg"
    TRANSFORMERS_BERT = "bert-base-uncased"
    TRANSFORMERS_LEGAL = "nlpaueb/legal-bert-base-uncased"
    OPENAI_GPT4 = "gpt-4"
    OPENAI_GPT35 = "gpt-3.5-turbo"


@dataclass
class IntelligenceConfig:
    """Configuration for AI intelligence features."""
    
    # NLP Models
    primary_nlp_model: AIModel = AIModel.SPACY_SM
    classification_model: Optional[AIModel] = AIModel.TRANSFORMERS_BERT
    legal_analysis_model: Optional[AIModel] = AIModel.TRANSFORMERS_LEGAL
    
    # Confidence Thresholds
    min_confidence_threshold: float = 0.4
    auto_approval_threshold: float = 0.8
    high_confidence_threshold: float = 0.9
    
    # Rule Generation Settings
    max_rules_per_document: int = 50
    enable_auto_approval: bool = False
    require_human_review: bool = True
    
    # Processing Limits
    max_document_size_mb: int = 10
    max_processing_time_seconds: int = 300
    batch_processing_enabled: bool = True
    
    # Supported Formats
    supported_formats: List[str] = None
    
    # API Keys (loaded from environment)
    openai_api_key: Optional[str] = None
    hugging_face_token: Optional[str] = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['.pdf', '.html', '.htm', '.txt', '.docx']
            
        # Load API keys from environment
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.hugging_face_token = os.getenv('HUGGING_FACE_TOKEN')


@dataclass
class RegulationConfig:
    """Configuration for specific regulation types."""
    name: str
    keywords: List[str]
    data_types: List[str]
    sections: List[str]
    severity_weights: Dict[str, float]
    confidence_adjustments: Dict[str, float]


# Pre-configured regulation settings
REGULATION_CONFIGS = {
    "gdpr": RegulationConfig(
        name="General Data Protection Regulation",
        keywords=[
            "personal data", "data subject", "processing", "consent", "lawful basis",
            "controller", "processor", "data protection officer", "impact assessment",
            "right to erasure", "right to rectification", "data portability"
        ],
        data_types=[
            "name", "email address", "phone number", "postal address",
            "ip address", "cookies", "device identifiers", "location data",
            "biometric data", "genetic data", "health data", "sexual orientation"
        ],
        sections=[
            "Article 5", "Article 6", "Article 7", "Article 9", "Article 17",
            "Article 20", "Article 25", "Article 32", "Article 35"
        ],
        severity_weights={
            "consent": 0.9,
            "sensitive data": 1.0,
            "children": 1.0,
            "automated processing": 0.8,
            "data transfer": 0.7
        },
        confidence_adjustments={
            "must": 0.3,
            "shall": 0.3,
            "required": 0.2,
            "prohibited": 0.4,
            "ensure": 0.2
        }
    ),
    
    "hipaa": RegulationConfig(
        name="Health Insurance Portability and Accountability Act",
        keywords=[
            "PHI", "protected health information", "covered entity", "business associate",
            "minimum necessary", "administrative safeguards", "physical safeguards",
            "technical safeguards", "breach notification", "risk assessment"
        ],
        data_types=[
            "medical record number", "health plan beneficiary number",
            "account number", "certificate number", "license number",
            "vehicle identifier", "device identifier", "web URL",
            "ip address", "biometric identifier", "photograph"
        ],
        sections=[
            "164.502", "164.506", "164.508", "164.512", "164.514",
            "164.520", "164.522", "164.524", "164.526", "164.528"
        ],
        severity_weights={
            "PHI disclosure": 1.0,
            "unauthorized access": 0.9,
            "minimum necessary": 0.8,
            "breach": 1.0,
            "safeguards": 0.7
        },
        confidence_adjustments={
            "required": 0.3,
            "permitted": 0.2,
            "prohibited": 0.4,
            "must": 0.3,
            "may": 0.1
        }
    ),
    
    "pci_dss": RegulationConfig(
        name="Payment Card Industry Data Security Standard",
        keywords=[
            "cardholder data", "sensitive authentication data", "payment card",
            "PAN", "primary account number", "card verification value",
            "magnetic stripe", "chip data", "PIN", "cryptographic keys"
        ],
        data_types=[
            "credit card number", "debit card number", "PAN", "CVV", "CVV2",
            "CVC", "CID", "PIN", "magnetic stripe data", "chip data"
        ],
        sections=[
            "Requirement 1", "Requirement 2", "Requirement 3", "Requirement 4",
            "Requirement 5", "Requirement 6", "Requirement 7", "Requirement 8",
            "Requirement 9", "Requirement 10", "Requirement 11", "Requirement 12"
        ],
        severity_weights={
            "cardholder data": 1.0,
            "authentication data": 1.0,
            "encryption": 0.9,
            "access control": 0.8,
            "monitoring": 0.7
        },
        confidence_adjustments={
            "must": 0.3,
            "required": 0.3,
            "should": 0.2,
            "recommended": 0.1,
            "prohibited": 0.4
        }
    )
}


def load_intelligence_config() -> IntelligenceConfig:
    """Load intelligence configuration with environment overrides."""
    config = IntelligenceConfig()
    
    # Override with environment variables
    config.min_confidence_threshold = float(
        os.getenv('JIMINI_AI_MIN_CONFIDENCE', config.min_confidence_threshold)
    )
    config.auto_approval_threshold = float(
        os.getenv('JIMINI_AI_AUTO_APPROVAL_THRESHOLD', config.auto_approval_threshold)
    )
    config.max_rules_per_document = int(
        os.getenv('JIMINI_AI_MAX_RULES', config.max_rules_per_document)
    )
    config.enable_auto_approval = os.getenv('JIMINI_AI_AUTO_APPROVAL', 'false').lower() == 'true'
    config.require_human_review = os.getenv('JIMINI_AI_HUMAN_REVIEW', 'true').lower() == 'true'
    
    return config


def get_regulation_config(regulation_type: str) -> Optional[RegulationConfig]:
    """Get configuration for a specific regulation type."""
    return REGULATION_CONFIGS.get(regulation_type.lower())


def validate_intelligence_setup() -> Dict[str, bool]:
    """Validate that AI/ML dependencies are properly installed."""
    status = {
        "spacy_available": False,
        "spacy_model_available": False,
        "transformers_available": False,
        "openai_available": False,
        "pdf_processing_available": False,
        "html_processing_available": False
    }
    
    try:
        import spacy
        status["spacy_available"] = True
        
        try:
            nlp = spacy.load("en_core_web_sm")
            status["spacy_model_available"] = True
        except OSError:
            pass
    except ImportError:
        pass
    
    try:
        import transformers
        status["transformers_available"] = True
    except ImportError:
        pass
    
    try:
        import openai
        status["openai_available"] = True
    except ImportError:
        pass
    
    try:
        import PyPDF2
        status["pdf_processing_available"] = True
    except ImportError:
        pass
    
    try:
        from bs4 import BeautifulSoup
        status["html_processing_available"] = True
    except ImportError:
        pass
    
    return status


def get_installation_instructions() -> Dict[str, str]:
    """Get installation instructions for missing dependencies."""
    return {
        "spacy": "pip install spacy",
        "spacy_model": "python -m spacy download en_core_web_sm",
        "transformers": "pip install transformers torch",
        "openai": "pip install openai",
        "pdf_processing": "pip install PyPDF2",
        "html_processing": "pip install beautifulsoup4",
        "legal_model": "pip install transformers && huggingface-hub download nlpaueb/legal-bert-base-uncased"
    }