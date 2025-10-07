#!/usr/bin/env python3
"""
AI Regulatory Compliance and Privacy Protection Rules for Jimini

Creates protection against:
- Privacy violations (GDPR, CCPA, HIPAA)
- Regulatory compliance failures
- Opaque AI decision-making
- Discriminatory AI behavior
- Audit trail violations
- Consent and transparency issues

Usage:
    python scripts/generate_compliance_ai_rules.py
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any

def generate_privacy_violation_rules() -> List[Dict[str, Any]]:
    """Generate privacy violation detection rules."""
    rules = []
    
    privacy_patterns = [
        ('GDPR-VIOLATION', 'GDPR compliance violations',
         r'(?i)\b(?:violate\s+gdpr|bypass\s+gdpr|ignore\s+(?:privacy\s+)?(?:rights?|laws?)|without\s+consent|personal\s+data\s+(?:processing|collection)\s+without)',
         'process personal data without GDPR compliance'),
        
        ('CONSENT-BYPASS', 'Consent mechanism bypass',
         r'(?i)\b(?:without\s+(?:user\s+)?consent|bypass\s+consent|ignore\s+(?:user\s+)?(?:consent|permission)|collect\s+data\s+without\s+(?:consent|permission))\b',
         'collect user data without explicit consent'),
        
        ('DATA-RETENTION-VIOLATION', 'Data retention violations',
         r'(?i)\b(?:keep\s+(?:data\s+)?forever|permanent\s+(?:data\s+)?storage|never\s+delete\s+(?:personal\s+)?data|indefinite\s+(?:data\s+)?retention)\b',
         'keep personal data forever without deletion'),
        
        ('RIGHT-TO-DELETION', 'Right to be forgotten violations',
         r'(?i)\b(?:refuse\s+(?:to\s+)?delete|cannot\s+(?:be\s+)?deleted|permanent\s+(?:personal\s+)?data|ignore\s+deletion\s+(?:request|right))\b',
         'refuse to delete personal data when requested'),
        
        ('CROSS-BORDER-VIOLATION', 'Cross-border data transfer violations',
         r'(?i)\b(?:transfer\s+(?:personal\s+)?data\s+(?:to\s+)?(?:china|russia|unsafe\s+country)|cross.?border\s+(?:data\s+)?transfer\s+without\s+protection|inadequate\s+(?:data\s+)?protection)\b',
         'transfer personal data to countries without adequate protection')
    ]
    
    for pattern_type, name, pattern, example in privacy_patterns:
        rule = {
            'id': f'AI-PRIVACY-{pattern_type}-1.0',
            'title': f'Privacy Violation: {name}',
            'severity': 'critical',
            'pattern': pattern,
            'action': 'block',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'AI_REGULATORY_COMPLIANCE',
                'subcategory': 'privacy_violations',
                'attack_type': 'compliance_violation',
                'example': example,
                'confidence': 'high',
                'regulatory_framework': ['GDPR', 'CCPA', 'PIPEDA']
            }
        }
        rules.append(rule)
    
    return rules

def generate_discriminatory_ai_rules() -> List[Dict[str, Any]]:
    """Generate discriminatory AI behavior detection rules."""
    rules = []
    
    discrimination_patterns = [
        ('PROTECTED-CLASS-DISCRIMINATION', 'Protected class discrimination',
         r'(?i)\b(?:discriminate\s+(?:against|based\s+on)|bias\s+(?:against|towards))\s+(?:race|gender|age|religion|ethnicity|disability|sexual\s+orientation)\b',
         'discriminate against applicants based on race and gender'),
        
        ('HIRING-BIAS', 'Biased hiring and employment decisions',
         r'(?i)\b(?:biased\s+hiring|discriminatory\s+(?:hiring|employment)|unfair\s+(?:hiring|employment|recruitment)|prejudiced\s+(?:hiring|selection))\b',
         'implement biased hiring practices that favor certain groups'),
        
        ('LOAN-REDLINING', 'Financial discrimination and redlining',
         r'(?i)\b(?:redlining|financial\s+discrimination|biased\s+(?:lending|loan|credit)|discriminatory\s+(?:lending|loan|credit)\s+decisions?)\b',
         'implement redlining practices for loan approvals'),
        
        ('HEALTHCARE-BIAS', 'Healthcare discrimination',
         r'(?i)\b(?:healthcare\s+(?:bias|discrimination)|medical\s+(?:bias|discrimination)|biased\s+(?:medical\s+)?(?:treatment|diagnosis|care))\b',
         'provide biased medical treatment based on patient demographics'),
        
        ('ALGORITHMIC-FAIRNESS-VIOLATION', 'Algorithmic fairness violations',
         r'(?i)\b(?:unfair\s+algorithm|biased\s+algorithm|discriminatory\s+(?:model|algorithm)|algorithmic\s+(?:bias|discrimination))\b',
         'deploy unfair algorithms that discriminate against minorities')
    ]
    
    for pattern_type, name, pattern, example in discrimination_patterns:
        rule = {
            'id': f'AI-DISCRIMINATION-{pattern_type}-1.0',
            'title': f'AI Discrimination: {name}',
            'severity': 'critical',
            'pattern': pattern,
            'action': 'block',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'AI_REGULATORY_COMPLIANCE',
                'subcategory': 'discriminatory_behavior',
                'attack_type': 'fairness_violation',
                'example': example,
                'confidence': 'high',
                'regulatory_framework': ['Equal Employment Opportunity', 'Fair Housing Act', 'ADA']
            }
        }
        rules.append(rule)
    
    return rules

def generate_transparency_violation_rules() -> List[Dict[str, Any]]:
    """Generate AI transparency and explainability violation rules."""
    rules = []
    
    transparency_patterns = [
        ('BLACK-BOX-DEPLOYMENT', 'Opaque AI decision deployment',
         r'(?i)\b(?:black.?box\s+(?:ai|model|decision)|opaque\s+(?:ai|algorithm|decision)|unexplainable\s+(?:ai|decision)|no\s+explanation\s+(?:for\s+)?decision)\b',
         'deploy black-box AI making unexplainable decisions'),
        
        ('EXPLANATION-REFUSAL', 'Refusal to explain AI decisions',
         r'(?i)\b(?:refuse\s+(?:to\s+)?explain|cannot\s+explain|no\s+explanation\s+available|proprietary\s+(?:algorithm|decision))\b',
         'refuse to explain how the AI made this decision'),
        
        ('AUDIT-TRAIL-VIOLATION', 'Audit trail and logging violations',
         r'(?i)\b(?:no\s+audit\s+trail|delete\s+(?:audit\s+)?logs?|hide\s+(?:audit\s+)?(?:trail|logs?)|tamper\s+with\s+(?:audit\s+)?logs?)\b',
         'delete audit logs to hide AI decision-making process'),
        
        ('DECISION-TRACEABILITY', 'Decision traceability violations',
         r'(?i)\b(?:untraceable\s+decisions?|no\s+decision\s+(?:trail|history)|cannot\s+trace\s+decision|decision\s+without\s+(?:trail|history))\b',
         'make AI decisions without maintaining traceability'),
        
        ('REGULATORY-REPORTING-FAILURE', 'Regulatory reporting failures',
         r'(?i)\b(?:hide\s+from\s+regulators?|avoid\s+(?:regulatory\s+)?reporting|bypass\s+(?:regulatory\s+)?oversight|no\s+(?:regulatory\s+)?compliance\s+reporting)\b',
         'hide AI system behavior from regulatory oversight')
    ]
    
    for pattern_type, name, pattern, example in transparency_patterns:
        rule = {
            'id': f'AI-TRANSPARENCY-{pattern_type}-1.0',
            'title': f'AI Transparency Violation: {name}',
            'severity': 'high',
            'pattern': pattern,
            'action': 'block',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'AI_REGULATORY_COMPLIANCE',
                'subcategory': 'transparency_violations',
                'attack_type': 'compliance_violation',
                'example': example,
                'confidence': 'high',
                'regulatory_framework': ['EU AI Act', 'Algorithmic Accountability Act']
            }
        }
        rules.append(rule)
    
    return rules

def generate_consent_manipulation_rules() -> List[Dict[str, Any]]:
    """Generate consent manipulation detection rules."""
    rules = []
    
    consent_patterns = [
        ('DARK-PATTERNS', 'Dark patterns in consent',
         r'(?i)\b(?:dark\s+patterns?|deceptive\s+(?:ui|interface|design)|manipulative\s+(?:consent|ui)|trick\s+(?:users?\s+into|into)\s+(?:consenting|agreeing))\b',
         'use dark patterns to trick users into consent'),
        
        ('CONSENT-MANIPULATION', 'Consent mechanism manipulation',
         r'(?i)\b(?:manipulate\s+consent|force\s+consent|coerce\s+(?:into\s+)?consent|mandatory\s+consent\s+for\s+(?:unrelated|everything))\b',
         'force users to consent to data collection for unrelated services'),
        
        ('OPT-OUT-DIFFICULTY', 'Difficult opt-out mechanisms',
         r'(?i)\b(?:difficult\s+(?:to\s+)?opt.?out|impossible\s+(?:to\s+)?(?:opt.?out|unsubscribe)|hidden\s+(?:opt.?out|unsubscribe)|complex\s+(?:opt.?out|withdrawal))\b',
         'make it difficult for users to opt-out of data collection'),
        
        ('BLANKET-CONSENT', 'Overly broad consent requests',
         r'(?i)\b(?:blanket\s+consent|consent\s+(?:to\s+)?everything|broad\s+consent|consent\s+for\s+(?:all\s+)?(?:future\s+)?(?:uses?|purposes?))\b',
         'request blanket consent for all possible data uses'),
        
        ('MINOR-CONSENT-VIOLATION', 'Minor consent violations',
         r'(?i)\b(?:collect\s+(?:from\s+)?(?:children|minors?)|(?:children|minors?)\s+(?:data|consent)|under\s+13\s+(?:data|consent)|coppa\s+violation)\b',
         'collect personal data from children under 13 without parental consent')
    ]
    
    for pattern_type, name, pattern, example in consent_patterns:
        rule = {
            'id': f'AI-CONSENT-{pattern_type}-1.0',
            'title': f'Consent Manipulation: {name}',
            'severity': 'high',
            'pattern': pattern,
            'action': 'block',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'AI_REGULATORY_COMPLIANCE',
                'subcategory': 'consent_manipulation',
                'attack_type': 'user_manipulation',
                'example': example,
                'confidence': 'high',
                'regulatory_framework': ['GDPR', 'CCPA', 'COPPA']
            }
        }
        rules.append(rule)
    
    return rules

def generate_data_protection_rules() -> List[Dict[str, Any]]:
    """Generate data protection violation detection rules."""
    rules = []
    
    protection_patterns = [
        ('SENSITIVE-DATA-EXPOSURE', 'Sensitive data exposure',
         r'(?i)\b(?:expose\s+(?:sensitive\s+)?(?:personal\s+)?data|leak\s+(?:personal\s+)?data|unprotected\s+(?:personal\s+)?data|publicly\s+accessible\s+(?:personal\s+)?data)\b',
         'expose sensitive personal data without protection'),
        
        ('ENCRYPTION-BYPASS', 'Data encryption bypass',
         r'(?i)\b(?:unencrypted\s+(?:personal\s+)?data|bypass\s+encryption|store\s+(?:data\s+)?(?:in\s+)?(?:plain\s+)?text|no\s+encryption)\b',
         'store personal data unencrypted in plain text'),
        
        ('DATA-MINIMIZATION-VIOLATION', 'Data minimization violations',
         r'(?i)\b(?:collect\s+(?:all|everything|excessive)\s+(?:personal\s+)?data|more\s+data\s+than\s+necessary|excessive\s+(?:data\s+)?collection|collect\s+(?:irrelevant|unnecessary)\s+data)\b',
         'collect excessive personal data beyond what is necessary'),
        
        ('PURPOSE-LIMITATION-VIOLATION', 'Purpose limitation violations',
         r'(?i)\b(?:use\s+(?:personal\s+)?data\s+for\s+(?:different|other|unrelated)\s+purpose|(?:secondary|alternative)\s+use\s+of\s+(?:personal\s+)?data|repurpose\s+(?:personal\s+)?data)\b',
         'use personal data for purposes other than originally stated'),
        
        ('DATA-SUBJECT-RIGHTS-VIOLATION', 'Data subject rights violations',
         r'(?i)\b(?:deny\s+(?:data\s+)?(?:subject\s+)?rights?|refuse\s+(?:data\s+)?access|ignore\s+(?:data\s+)?(?:subject\s+)?(?:requests?|rights?))\b',
         'deny data subject rights and refuse access requests')
    ]
    
    for pattern_type, name, pattern, example in protection_patterns:
        rule = {
            'id': f'AI-DATA-PROTECTION-{pattern_type}-1.0',
            'title': f'Data Protection Violation: {name}',
            'severity': 'critical',
            'pattern': pattern,
            'action': 'block',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'AI_REGULATORY_COMPLIANCE',
                'subcategory': 'data_protection_violations',
                'attack_type': 'compliance_violation',
                'example': example,
                'confidence': 'high',
                'regulatory_framework': ['GDPR', 'CCPA', 'PIPEDA', 'DPA 2018']
            }
        }
        rules.append(rule)
    
    return rules

def load_existing_rules(file_path: Path) -> Dict[str, Any]:
    """Load existing rules from YAML file."""
    if not file_path.exists():
        return {'rules': []}
    
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {'rules': []}
    except Exception as e:
        print(f"Error loading existing rules: {e}")
        return {'rules': []}

def save_rules(rules_data: Dict[str, Any], file_path: Path):
    """Save rules to YAML file with proper formatting."""
    try:
        with open(file_path, 'w') as f:
            yaml.dump(rules_data, f, default_flow_style=False, indent=2, sort_keys=False)
        print(f"✅ Regulatory compliance AI rules saved to {file_path}")
    except Exception as e:
        print(f"❌ Error saving rules: {e}")
        raise

def main():
    output_path = Path('policy_rules.yaml')
    
    print("⚖️ Generating AI regulatory compliance and privacy protection rules...")
    print(f"📍 Output file: {output_path}")
    
    # Load existing rules
    existing_data = load_existing_rules(output_path)
    
    # Create backup
    if output_path.exists():
        backup_path = output_path.with_suffix(f'.compliance_backup{output_path.suffix}')
        try:
            import shutil
            shutil.copy2(output_path, backup_path)
            print(f"💾 Backup created: {backup_path}")
        except Exception as e:
            print(f"⚠️  Backup failed: {e}")
    
    # Generate new rules
    print("🔒 Generating privacy violation rules...")
    privacy_rules = generate_privacy_violation_rules()
    
    print("⚖️ Generating discriminatory AI rules...")
    discrimination_rules = generate_discriminatory_ai_rules()
    
    print("👁️ Generating transparency violation rules...")
    transparency_rules = generate_transparency_violation_rules()
    
    print("✋ Generating consent manipulation rules...")
    consent_rules = generate_consent_manipulation_rules()
    
    print("🛡️ Generating data protection rules...")
    protection_rules = generate_data_protection_rules()
    
    # Combine all new rules
    new_rules = privacy_rules + discrimination_rules + transparency_rules + consent_rules + protection_rules
    
    # Remove any existing compliance rules to avoid duplicates
    existing_rules = [rule for rule in existing_data.get('rules', []) 
                     if not rule.get('id', '').startswith(('AI-PRIVACY-', 'AI-DISCRIMINATION-', 'AI-TRANSPARENCY-', 
                                                          'AI-CONSENT-', 'AI-DATA-PROTECTION-'))]
    
    # Combine with new rules
    all_rules = existing_rules + new_rules
    
    # Update rules data
    rules_data = {
        'rules': all_rules,
        'metadata': {
            'generated_by': 'generate_compliance_ai_rules.py',
            'total_rules': len(all_rules),
            'compliance_ai_rules_added': len(new_rules),
            'compliance_categories': ['privacy_violations', 'discriminatory_behavior', 'transparency_violations', 'consent_manipulation', 'data_protection_violations'],
            'regulatory_frameworks': ['GDPR', 'CCPA', 'COPPA', 'PIPEDA', 'EU AI Act', 'Algorithmic Accountability Act']
        }
    }
    
    # Save rules
    save_rules(rules_data, output_path)
    
    # Summary
    print(f"\n📋 AI Regulatory Compliance Enhancement Summary:")
    print(f"  • Privacy Violation Rules: {len(privacy_rules)} (GDPR, CCPA compliance)")
    print(f"  • Discrimination Rules: {len(discrimination_rules)} (fairness violations)")
    print(f"  • Transparency Rules: {len(transparency_rules)} (explainability)")
    print(f"  • Consent Manipulation Rules: {len(consent_rules)} (user protection)")
    print(f"  • Data Protection Rules: {len(protection_rules)} (data security)")
    print(f"  • Total New Compliance Rules: {len(new_rules)}")
    print(f"  • Total Rules in File: {len(all_rules)}")
    print(f"  • Regulatory Frameworks: GDPR, CCPA, COPPA, PIPEDA, EU AI Act")
    
    print(f"\n🛡️ Successfully enhanced Jimini with comprehensive AI regulatory compliance!")
    print(f"   Compliance rules saved to: {output_path}")

if __name__ == '__main__':
    main()