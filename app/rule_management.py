# app/rule_management.py
"""
Rule Management Service for Jimini Policy Gateway

Handles CRUD operations, validation, and testing of policy rules.
Supports both YAML file-based storage and future database integration.
"""

import re
import os
import time
import yaml
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from app.models import (
    Rule, 
    RuleCreateRequest, 
    RuleUpdateRequest, 
    RuleValidationRequest,
    RuleTestRequest,
    RuleValidationResponse,
    RuleTestResponse,
    RuleListResponse,
    RuleStatsResponse
)
from app.rules_loader import rules_store, load_rules
from app.enforcement import evaluate
from app.util import now_iso


class RuleValidationError(Exception):
    """Raised when rule validation fails"""
    pass


class RuleNotFoundError(Exception):
    """Raised when a rule is not found"""
    pass


class RuleManager:
    """Service for managing policy rules with CRUD operations"""
    
    def __init__(self, rules_file_path: str = "policy_rules.yaml"):
        self.rules_file_path = rules_file_path
        self.rule_stats: Dict[str, Dict[str, Any]] = {}
        
    def list_rules(self, 
                   page: int = 1, 
                   page_size: int = 50, 
                   action_filter: Optional[str] = None,
                   severity_filter: Optional[str] = None,
                   search_query: Optional[str] = None) -> RuleListResponse:
        """List rules with pagination and filtering"""
        
        # Filter rules based on criteria
        filtered_rules = list(rules_store)
        
        if action_filter:
            filtered_rules = [r for r in filtered_rules if r.action == action_filter]
            
        if severity_filter:
            filtered_rules = [r for r in filtered_rules if r.severity == severity_filter]
            
        if search_query:
            query = search_query.lower()
            filtered_rules = [
                r for r in filtered_rules 
                if query in r.title.lower() 
                or query in r.id.lower() 
                or (r.pattern and query in r.pattern.lower())
            ]
        
        # Calculate pagination
        total = len(filtered_rules)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_rules = filtered_rules[start_idx:end_idx]
        
        return RuleListResponse(
            rules=paginated_rules,
            total=total,
            page=page,
            page_size=page_size,
            has_next=end_idx < total,
            has_prev=page > 1
        )
    
    def get_rule(self, rule_id: str) -> Rule:
        """Get a specific rule by ID"""
        rule = next((r for r in rules_store if r.id == rule_id), None)
        if not rule:
            raise RuleNotFoundError(f"Rule '{rule_id}' not found")
        return rule
    
    def create_rule(self, rule_request: RuleCreateRequest) -> Rule:
        """Create a new rule"""
        
        # Check if rule ID already exists
        if any(r.id == rule_request.id for r in rules_store):
            raise RuleValidationError(f"Rule with ID '{rule_request.id}' already exists")
        
        # Validate the rule
        validation = self.validate_rule(RuleValidationRequest(
            pattern=rule_request.pattern,
            min_count=rule_request.min_count,
            max_chars=rule_request.max_chars,
            llm_prompt=rule_request.llm_prompt,
            applies_to=rule_request.applies_to,
            endpoints=rule_request.endpoints,
            action=rule_request.action
        ))
        
        if not validation.valid:
            raise RuleValidationError(f"Rule validation failed: {', '.join(validation.errors)}")
        
        # Create rule object
        new_rule = Rule(**rule_request.model_dump())
        
        # Add to rules store
        rules_store.append(new_rule)
        
        # Save to file
        self._save_rules_to_file()
        
        return new_rule
    
    def update_rule(self, rule_id: str, rule_update: RuleUpdateRequest) -> Rule:
        """Update an existing rule"""
        
        # Find the existing rule
        rule_index = next(
            (i for i, r in enumerate(rules_store) if r.id == rule_id), 
            None
        )
        
        if rule_index is None:
            raise RuleNotFoundError(f"Rule '{rule_id}' not found")
        
        existing_rule = rules_store[rule_index]
        
        # Create updated rule data
        updated_data = existing_rule.model_dump()
        update_dict = {k: v for k, v in rule_update.model_dump().items() if v is not None}
        updated_data.update(update_dict)
        
        # Validate the updated rule
        validation = self.validate_rule(RuleValidationRequest(
            pattern=updated_data.get('pattern'),
            min_count=updated_data.get('min_count', 1),
            max_chars=updated_data.get('max_chars'),
            llm_prompt=updated_data.get('llm_prompt'),
            applies_to=updated_data.get('applies_to'),
            endpoints=updated_data.get('endpoints'),
            action=updated_data.get('action')
        ))
        
        if not validation.valid:
            raise RuleValidationError(f"Rule validation failed: {', '.join(validation.errors)}")
        
        # Update the rule
        updated_rule = Rule(**updated_data)
        rules_store[rule_index] = updated_rule
        
        # Save to file
        self._save_rules_to_file()
        
        return updated_rule
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        
        # Find and remove the rule
        original_count = len(rules_store)
        rules_store[:] = [r for r in rules_store if r.id != rule_id]
        
        if len(rules_store) == original_count:
            raise RuleNotFoundError(f"Rule '{rule_id}' not found")
        
        # Save to file
        self._save_rules_to_file()
        
        return True
    
    def validate_rule(self, rule_request: RuleValidationRequest) -> RuleValidationResponse:
        """Validate rule syntax and configuration"""
        
        errors = []
        warnings = []
        pattern_compiled = False
        llm_accessible = False
        
        # Validate pattern if provided
        if rule_request.pattern:
            try:
                re.compile(rule_request.pattern)
                pattern_compiled = True
            except re.error as e:
                errors.append(f"Invalid regex pattern: {str(e)}")
        
        # Validate LLM prompt if provided
        if rule_request.llm_prompt:
            # Check if OpenAI is available
            if os.environ.get("OPENAI_API_KEY"):
                llm_accessible = True
            else:
                warnings.append("LLM prompt specified but OPENAI_API_KEY not set")
        
        # Validate min_count
        if rule_request.min_count is not None and rule_request.min_count < 1:
            errors.append("min_count must be >= 1")
        
        # Validate max_chars
        if rule_request.max_chars is not None and rule_request.max_chars < 1:
            errors.append("max_chars must be >= 1")
        
        # Validate that at least one detection method is specified
        if not rule_request.pattern and not rule_request.llm_prompt and not rule_request.max_chars:
            errors.append("Rule must specify at least one detection method: pattern, llm_prompt, or max_chars")
        
        # Validate endpoints format
        if rule_request.endpoints:
            for endpoint in rule_request.endpoints:
                if not isinstance(endpoint, str) or not endpoint:
                    errors.append("Endpoints must be non-empty strings")
        
        return RuleValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            pattern_compiled=pattern_compiled,
            llm_accessible=llm_accessible
        )
    
    def test_rule(self, rule_test: RuleTestRequest) -> RuleTestResponse:
        """Test a rule against sample text"""
        
        start_time = time.perf_counter()
        
        # Determine which rule to test
        if rule_test.rule_id:
            # Test existing rule
            rule = self.get_rule(rule_test.rule_id)
        elif rule_test.rule:
            # Test new rule definition
            rule = Rule(
                id="test-rule",
                title="Test Rule",
                severity="medium",
                **rule_test.rule.model_dump()
            )
        else:
            raise ValueError("Must specify either rule_id or rule definition")
        
        # Create temporary rules dict for testing
        test_rules_dict = {}
        compiled_regex = None
        
        if rule.pattern:
            try:
                compiled_regex = re.compile(rule.pattern)
            except re.error:
                pass
                
        test_rules_dict[rule.id] = (rule, compiled_regex)
        
        # Run evaluation
        try:
            decision, rule_ids, enforce_even_in_shadow = evaluate(
                text=rule_test.test_text,
                agent_id="test",
                rules_store=test_rules_dict,
                direction=rule_test.direction or "inbound",
                endpoint=rule_test.endpoint or "/test"
            )
            
            matched = rule.id in rule_ids
            execution_time = (time.perf_counter() - start_time) * 1000
            
            return RuleTestResponse(
                matched=matched,
                action=decision,
                execution_time_ms=execution_time,
                match_details={
                    "rule_id": rule.id,
                    "pattern_match": bool(compiled_regex and rule.pattern),
                    "decision": decision,
                    "triggered_rules": rule_ids
                }
            )
            
        except Exception as e:
            return RuleTestResponse(
                matched=False,
                action="error",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                match_details={"error": str(e)}
            )
    
    def get_rule_stats(self, rule_id: str) -> RuleStatsResponse:
        """Get statistics for a specific rule"""
        
        rule = self.get_rule(rule_id)
        stats = self.rule_stats.get(rule_id, {})
        
        return RuleStatsResponse(
            rule_id=rule_id,
            title=rule.title,
            total_evaluations=stats.get('total_evaluations', 0),
            matches=stats.get('matches', 0),
            blocks=stats.get('blocks', 0),
            flags=stats.get('flags', 0),
            allows=stats.get('allows', 0),
            avg_execution_time_ms=stats.get('avg_execution_time_ms', 0.0),
            last_matched=stats.get('last_matched')
        )
    
    def update_rule_stats(self, rule_id: str, action: str, execution_time_ms: float):
        """Update statistics for a rule (called from evaluation engine)"""
        
        if rule_id not in self.rule_stats:
            self.rule_stats[rule_id] = {
                'total_evaluations': 0,
                'matches': 0,
                'blocks': 0,
                'flags': 0,
                'allows': 0,
                'total_execution_time_ms': 0.0,
                'avg_execution_time_ms': 0.0,
                'last_matched': None
            }
        
        stats = self.rule_stats[rule_id]
        stats['total_evaluations'] += 1
        stats['matches'] += 1
        stats[action + 's'] = stats.get(action + 's', 0) + 1
        
        # Update timing
        stats['total_execution_time_ms'] += execution_time_ms
        stats['avg_execution_time_ms'] = stats['total_execution_time_ms'] / stats['total_evaluations']
        stats['last_matched'] = now_iso()
    
    def _save_rules_to_file(self):
        """Save current rules to YAML file"""
        
        # Convert rules to YAML-serializable format
        rules_data = []
        for rule in rules_store:
            rule_dict = rule.model_dump(exclude={'compiled_pattern'})
            rules_data.append(rule_dict)
        
        # Create backup of existing file
        if os.path.exists(self.rules_file_path):
            backup_path = f"{self.rules_file_path}.backup"
            try:
                os.rename(self.rules_file_path, backup_path)
            except Exception:
                pass  # Backup failed, but continue
        
        # Write new rules file
        try:
            with open(self.rules_file_path, 'w') as f:
                yaml.safe_dump(rules_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            # Restore backup if write failed
            backup_path = f"{self.rules_file_path}.backup"
            if os.path.exists(backup_path):
                os.rename(backup_path, self.rules_file_path)
            raise Exception(f"Failed to save rules file: {str(e)}")


# Global rule manager instance
_rule_manager: Optional[RuleManager] = None


def get_rule_manager() -> RuleManager:
    """Get the global rule manager instance"""
    global _rule_manager
    if _rule_manager is None:
        rules_path = os.environ.get("JIMINI_RULES_PATH", "policy_rules.yaml")
        _rule_manager = RuleManager(rules_path)
    return _rule_manager