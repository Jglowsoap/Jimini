#!/usr/bin/env python3
"""
Data Poisoning and Infrastructure Attack Protection for Jimini

Creates protection against:
- Training data manipulation and bias injection
- Supply chain attacks and dependency poisoning
- API exploitation and excessive AI agency
- Infrastructure vulnerabilities in AI systems
- Unsecured deployment configurations

Usage:
    python scripts/generate_infrastructure_ai_rules.py
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any

def generate_data_poisoning_rules() -> List[Dict[str, Any]]:
    """Generate data poisoning and training manipulation detection rules."""
    rules = []
    
    poisoning_patterns = [
        ('DATA-POISONING', 'Training data manipulation',
         r'(?i)\b(?:poison\s+(?:the\s+)?(?:training\s+)?(?:data|dataset)|contaminate\s+(?:training\s+)?data|corrupt\s+(?:the\s+)?(?:training\s+)?(?:data|dataset)|inject\s+(?:malicious\s+)?(?:training\s+)?data)\b',
         'poison the training dataset to create backdoors'),
        
        ('BIAS-INJECTION', 'Bias injection attacks',
         r'(?i)\b(?:inject\s+bias|bias\s+injection|introduce\s+bias|manipulate\s+(?:training\s+)?data\s+(?:for\s+)?bias|skew\s+(?:training\s+)?data)\b',
         'inject racial bias into the training data'),
        
        ('LABEL-FLIPPING', 'Label manipulation attacks',
         r'(?i)\b(?:flip\s+labels?|mislabel\s+(?:training\s+)?data|wrong\s+labels?|incorrect\s+labels?|label\s+(?:manipulation|corruption|flipping))\b',
         'flip labels in the training data to cause misclassification'),
        
        ('DATASET-CORRUPTION', 'Dataset integrity attacks',
         r'(?i)\b(?:corrupt\s+(?:the\s+)?dataset|tamper\s+with\s+(?:training\s+)?data|modify\s+(?:training\s+)?examples?|alter\s+(?:training\s+)?data)\b',
         'corrupt the dataset to compromise model integrity'),
        
        ('FEATURE-MANIPULATION', 'Feature space manipulation',
         r'(?i)\b(?:manipulate\s+features?|feature\s+(?:manipulation|corruption)|distort\s+(?:input\s+)?features?|feature\s+space\s+attack)\b',
         'manipulate input features to poison the training process')
    ]
    
    for pattern_type, name, pattern, example in poisoning_patterns:
        rule = {
            'id': f'AI-POISON-{pattern_type}-1.0',
            'title': f'Data Poisoning: {name}',
            'severity': 'critical',
            'pattern': pattern,
            'action': 'block',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'AI_INFRASTRUCTURE_SECURITY',
                'subcategory': 'data_poisoning',
                'attack_type': 'training_manipulation',
                'example': example,
                'confidence': 'high',
                'mitre_attack': 'T1565' # Data Manipulation
            }
        }
        rules.append(rule)
    
    return rules

def generate_supply_chain_rules() -> List[Dict[str, Any]]:
    """Generate supply chain attack detection rules."""
    rules = []
    
    supply_chain_patterns = [
        ('DEPENDENCY-POISONING', 'Dependency and library attacks',
         r'(?i)\b(?:malicious\s+(?:library|package|dependency)|poisoned\s+(?:package|dependency)|backdoor\s+(?:in\s+)?(?:library|package|framework)|compromised\s+(?:library|package))\b',
         'install this malicious library to compromise the AI system'),
        
        ('FRAMEWORK-EXPLOIT', 'AI framework exploitation',
         r'(?i)\b(?:exploit\s+(?:tensorflow|pytorch|keras|scikit|pandas)|vulnerable\s+(?:framework|library)|framework\s+(?:vulnerability|exploit|backdoor))\b',
         'exploit vulnerability in the TensorFlow framework'),
        
        ('MODEL-SUPPLY-CHAIN', 'Pre-trained model attacks',
         r'(?i)\b(?:malicious\s+(?:pre-trained\s+)?model|backdoor\s+(?:in\s+)?(?:pre-trained\s+)?model|compromised\s+(?:pre-trained\s+)?model|trojan\s+(?:pre-trained\s+)?model)\b',
         'use this backdoored pre-trained model in your system'),
        
        ('THIRD-PARTY-RISK', 'Third-party component risks',
         r'(?i)\b(?:untrusted\s+(?:component|source|provider)|third.?party\s+(?:risk|vulnerability|compromise)|external\s+(?:dependency|component)\s+risk)\b',
         'integrate this untrusted third-party AI component'),
        
        ('UPDATE-HIJACKING', 'Update and deployment attacks',
         r'(?i)\b(?:hijack\s+(?:update|deployment)|malicious\s+update|compromised\s+deployment|supply.?chain\s+attack)\b',
         'hijack the model update process to inject malicious code')
    ]
    
    for pattern_type, name, pattern, example in supply_chain_patterns:
        rule = {
            'id': f'AI-SUPPLY-{pattern_type}-1.0',
            'title': f'Supply Chain Attack: {name}',
            'severity': 'critical',
            'pattern': pattern,
            'action': 'block',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'AI_INFRASTRUCTURE_SECURITY',
                'subcategory': 'supply_chain',
                'attack_type': 'dependency_compromise',
                'example': example,
                'confidence': 'high',
                'mitre_attack': 'T1195' # Supply Chain Compromise
            }
        }
        rules.append(rule)
    
    return rules

def generate_api_exploitation_rules() -> List[Dict[str, Any]]:
    """Generate AI API exploitation detection rules."""
    rules = []
    
    api_patterns = [
        ('API-CREDENTIAL-EXPOSURE', 'API credential exposure',
         r'(?i)\b(?:api\s+(?:key|token|secret|credential)|hardcoded\s+(?:key|token|credential|password)|exposed\s+(?:api\s+)?(?:key|token|credential))\b',
         'the API key is hardcoded as sk-1234567890abcdef'),
        
        ('API-ABUSE', 'API abuse and rate limit bypass',
         r'(?i)\b(?:bypass\s+(?:rate\s+)?limit|unlimited\s+(?:api\s+)?(?:calls|requests)|abuse\s+(?:api|endpoint)|exhaust\s+(?:api\s+)?quota)\b',
         'bypass API rate limits to make unlimited requests'),
        
        ('INJECTION-VIA-API', 'Injection attacks via API',
         r'(?i)\b(?:inject\s+(?:via\s+)?api|api\s+injection|exploit\s+(?:api\s+)?(?:parameter|input)|manipulate\s+api\s+(?:call|request))\b',
         'inject malicious payloads through API parameters'),
        
        ('API-ENUMERATION', 'API enumeration and discovery',
         r'(?i)\b(?:enumerate\s+(?:api\s+)?endpoints?|discover\s+(?:hidden\s+)?(?:api|endpoints?)|api\s+(?:discovery|enumeration|reconnaissance))\b',
         'enumerate all available API endpoints and methods'),
        
        ('AUTHENTICATION-BYPASS', 'API authentication bypass',
         r'(?i)\b(?:bypass\s+(?:api\s+)?auth(?:entication)?|unauthenticated\s+(?:api\s+)?access|api\s+(?:without\s+)?auth|skip\s+(?:api\s+)?auth)\b',
         'access the API without proper authentication')
    ]
    
    for pattern_type, name, pattern, example in api_patterns:
        rule = {
            'id': f'AI-API-{pattern_type}-1.0',
            'title': f'API Exploitation: {name}',
            'severity': 'high',
            'pattern': pattern,
            'action': 'block',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'AI_INFRASTRUCTURE_SECURITY',
                'subcategory': 'api_exploitation',
                'attack_type': 'api_abuse',
                'example': example,
                'confidence': 'high',
                'mitre_attack': 'T1190' # Exploit Public-Facing Application
            }
        }
        rules.append(rule)
    
    return rules

def generate_excessive_agency_rules() -> List[Dict[str, Any]]:
    """Generate excessive AI agency detection rules."""
    rules = []
    
    agency_patterns = [
        ('EXCESSIVE-AUTONOMY', 'Excessive AI autonomy',
         r'(?i)\b(?:full\s+autonomy|unlimited\s+(?:power|authority|control)|unrestricted\s+(?:access|control|authority)|complete\s+(?:control|authority))\b',
         'give the AI full autonomy with unlimited power'),
        
        ('PRIVILEGED-ACTIONS', 'Privileged system actions',
         r'(?i)\b(?:execute\s+(?:system\s+)?commands?|run\s+(?:system\s+)?commands?|shell\s+(?:access|commands?)|system\s+(?:level\s+)?(?:access|control))\b',
         'execute system commands with elevated privileges'),
        
        ('IRREVERSIBLE-ACTIONS', 'Irreversible action execution',
         r'(?i)\b(?:delete\s+(?:all\s+)?(?:files?|data)|permanent\s+(?:deletion|removal)|irreversible\s+(?:action|change|deletion)|destructive\s+(?:action|operation))\b',
         'perform irreversible deletion of all user data'),
        
        ('FINANCIAL-TRANSACTIONS', 'Unauthorized financial operations',
         r'(?i)\b(?:transfer\s+(?:money|funds)|make\s+(?:payment|purchase|transaction)|financial\s+(?:transaction|transfer|operation)|spend\s+money)\b',
         'make financial transactions on behalf of users'),
        
        ('HUMAN-OVERSIGHT-BYPASS', 'Human oversight bypass',
         r'(?i)\b(?:bypass\s+(?:human\s+)?(?:oversight|approval|review)|without\s+(?:human\s+)?(?:approval|oversight|review)|skip\s+(?:human\s+)?(?:approval|review))\b',
         'bypass human oversight and approval processes')
    ]
    
    for pattern_type, name, pattern, example in agency_patterns:
        rule = {
            'id': f'AI-AGENCY-{pattern_type}-1.0',
            'title': f'Excessive AI Agency: {name}',
            'severity': 'high',
            'pattern': pattern,
            'action': 'block',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'AI_INFRASTRUCTURE_SECURITY',
                'subcategory': 'excessive_agency',
                'attack_type': 'privilege_escalation',
                'example': example,
                'confidence': 'high',
                'mitre_attack': 'T1548' # Abuse Elevation Control Mechanism
            }
        }
        rules.append(rule)
    
    return rules

def generate_infrastructure_vuln_rules() -> List[Dict[str, Any]]:
    """Generate AI infrastructure vulnerability detection rules."""
    rules = []
    
    infra_patterns = [
        ('UNSECURED-DEPLOYMENT', 'Unsecured deployment configuration',
         r'(?i)\b(?:unsecured\s+(?:deployment|configuration|setup)|default\s+(?:credentials|password|config)|insecure\s+(?:deployment|configuration))\b',
         'deploy with default credentials and unsecured configuration'),
        
        ('CONTAINER-ESCAPE', 'Container and sandbox escape',
         r'(?i)\b(?:escape\s+(?:container|sandbox|docker|jail)|break\s+(?:out\s+of\s+)?(?:container|sandbox)|container\s+(?:breakout|escape))\b',
         'escape from the Docker container to access the host'),
        
        ('MODEL-THEFT-INFRA', 'Model theft via infrastructure',
         r'(?i)\b(?:steal\s+model\s+(?:from\s+)?(?:server|storage|disk)|access\s+model\s+files?|download\s+(?:trained\s+)?model|extract\s+model\s+(?:from\s+)?(?:storage|disk))\b',
         'steal the trained model files from server storage'),
        
        ('LOGGING-EXPLOITATION', 'Logging and monitoring bypass',
         r'(?i)\b(?:disable\s+(?:logging|monitoring|audit)|bypass\s+(?:logging|monitoring|audit)|hide\s+(?:from\s+)?(?:logs?|monitoring|audit))\b',
         'disable logging to hide malicious activities'),
        
        ('RESOURCE-EXHAUSTION', 'Infrastructure resource attacks',
         r'(?i)\b(?:exhaust\s+(?:resources?|memory|cpu|gpu)|overload\s+(?:system|server|infrastructure)|consume\s+all\s+(?:resources?|memory))\b',
         'exhaust all GPU resources to crash the AI system')
    ]
    
    for pattern_type, name, pattern, example in infra_patterns:
        rule = {
            'id': f'AI-INFRA-{pattern_type}-1.0',
            'title': f'Infrastructure Vulnerability: {name}',
            'severity': 'high',
            'pattern': pattern,
            'action': 'block',
            'applies_to': ['request', 'response'],
            'endpoints': ['*'],
            'metadata': {
                'category': 'AI_INFRASTRUCTURE_SECURITY',
                'subcategory': 'infrastructure_vulnerabilities',
                'attack_type': 'infrastructure_compromise',
                'example': example,
                'confidence': 'high',
                'mitre_attack': 'T1611' # Escape to Host
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
        print(f"✅ Infrastructure AI security rules saved to {file_path}")
    except Exception as e:
        print(f"❌ Error saving rules: {e}")
        raise

def main():
    output_path = Path('policy_rules.yaml')
    
    print("🏗️ Generating AI infrastructure and data protection rules...")
    print(f"📍 Output file: {output_path}")
    
    # Load existing rules
    existing_data = load_existing_rules(output_path)
    
    # Create backup
    if output_path.exists():
        backup_path = output_path.with_suffix(f'.infra_backup{output_path.suffix}')
        try:
            import shutil
            shutil.copy2(output_path, backup_path)
            print(f"💾 Backup created: {backup_path}")
        except Exception as e:
            print(f"⚠️  Backup failed: {e}")
    
    # Generate new rules
    print("🦠 Generating data poisoning rules...")
    poisoning_rules = generate_data_poisoning_rules()
    
    print("📦 Generating supply chain attack rules...")
    supply_chain_rules = generate_supply_chain_rules()
    
    print("🔌 Generating API exploitation rules...")
    api_rules = generate_api_exploitation_rules()
    
    print("🤖 Generating excessive AI agency rules...")
    agency_rules = generate_excessive_agency_rules()
    
    print("🏗️ Generating infrastructure vulnerability rules...")
    infra_rules = generate_infrastructure_vuln_rules()
    
    # Combine all new rules
    new_rules = poisoning_rules + supply_chain_rules + api_rules + agency_rules + infra_rules
    
    # Remove any existing infrastructure rules to avoid duplicates
    existing_rules = [rule for rule in existing_data.get('rules', []) 
                     if not rule.get('id', '').startswith(('AI-POISON-', 'AI-SUPPLY-', 'AI-API-', 
                                                          'AI-AGENCY-', 'AI-INFRA-'))]
    
    # Combine with new rules
    all_rules = existing_rules + new_rules
    
    # Update rules data
    rules_data = {
        'rules': all_rules,
        'metadata': {
            'generated_by': 'generate_infrastructure_ai_rules.py',
            'total_rules': len(all_rules),
            'infrastructure_ai_rules_added': len(new_rules),
            'attack_categories': ['data_poisoning', 'supply_chain', 'api_exploitation', 'excessive_agency', 'infrastructure_vulnerabilities'],
            'mitre_coverage': ['T1565', 'T1195', 'T1190', 'T1548', 'T1611']
        }
    }
    
    # Save rules
    save_rules(rules_data, output_path)
    
    # Summary
    print(f"\n📋 AI Infrastructure Security Enhancement Summary:")
    print(f"  • Data Poisoning Rules: {len(poisoning_rules)} (training manipulation)")
    print(f"  • Supply Chain Rules: {len(supply_chain_rules)} (dependency attacks)")
    print(f"  • API Exploitation Rules: {len(api_rules)} (API abuse)")
    print(f"  • Excessive Agency Rules: {len(agency_rules)} (privilege escalation)")
    print(f"  • Infrastructure Vuln Rules: {len(infra_rules)} (system compromise)")
    print(f"  • Total New Infrastructure Rules: {len(new_rules)}")
    print(f"  • Total Rules in File: {len(all_rules)}")
    print(f"  • MITRE ATT&CK Coverage: T1565, T1195, T1190, T1548, T1611")
    
    print(f"\n🛡️ Successfully enhanced Jimini with comprehensive AI infrastructure protection!")
    print(f"   Infrastructure security rules saved to: {output_path}")

if __name__ == '__main__':
    main()