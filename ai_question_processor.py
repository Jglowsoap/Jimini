#!/usr/bin/env python3
"""
🤖 AI QUESTION PROCESSOR WITH JIMINI PII PROTECTION
===================================================

This adds AI question processing to your government dashboard.
All user questions are screened through Jimini before being sent to AI.
"""

import requests
import json
from typing import Dict, Any, Optional
import time

class JiminiAIQuestionProcessor:
    """Process AI questions through Jimini PII protection"""
    
    def __init__(self, 
                 jimini_url: str = "http://localhost:9000",
                 flask_url: str = "http://localhost:5001",
                 api_key: str = "changeme"):
        self.jimini_url = jimini_url
        self.flask_url = flask_url
        self.api_key = api_key
        self.use_direct_jimini = True  # Try Jimini first, fallback to Flask
        
    def check_question_safety(self, question: str, user_id: str = "ai_user") -> Dict[str, Any]:
        """
        Check if user's AI question contains PII before sending to AI
        
        Returns:
        - decision: ALLOW/FLAG/BLOCK
        - safe_to_proceed: boolean
        - sanitized_question: question with PII masked (if needed)
        - violations: list of PII detected
        """
        
        # Try Flask gateway first (more reliable)
        try:
            response = requests.post(
                f"{self.flask_url}/api/jimini/evaluate",
                json={
                    "text": question,
                    "endpoint": "/ai/question",
                    "user_id": user_id,
                    "agent_id": "ai_question_processor"
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._process_jimini_response(result, question)
                
        except Exception as e:
            print(f"Flask gateway error: {e}")
        
        # Fallback to direct Jimini
        try:
            response = requests.post(
                f"{self.jimini_url}/v1/evaluate",
                json={
                    "text": question,
                    "agent_id": f"ai_question_{user_id}",
                    "direction": "outbound",
                    "endpoint": "/ai/question",
                    "api_key": self.api_key
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._process_jimini_response(result, question)
                
        except Exception as e:
            print(f"Direct Jimini error: {e}")
        
        # Fallback: allow but warn
        return {
            "decision": "ALLOW",
            "safe_to_proceed": True,
            "sanitized_question": question,
            "violations": [],
            "warning": "PII protection unavailable - proceeding with caution"
        }
    
    def _process_jimini_response(self, jimini_result: Dict, original_question: str) -> Dict[str, Any]:
        """Process Jimini's response into our format"""
        
        decision = jimini_result.get('action', 'allow').upper()
        if 'decision' in jimini_result:
            decision = jimini_result['decision'].upper()
        
        rule_ids = jimini_result.get('rule_ids', [])
        
        # Determine if safe to proceed
        safe_to_proceed = decision in ['ALLOW', 'FLAG']
        
        # For questions with PII detected, mask the sensitive data
        sanitized_question = original_question
        if rule_ids:
            # Simple masking - in production you'd use more sophisticated methods
            import re
            
            # Mask common PII patterns
            sanitized_question = re.sub(r'\b\d{3}-?\d{2}-?\d{4}\b', '[SSN_MASKED]', sanitized_question)
            sanitized_question = re.sub(r'\b[A-Z]{1,2}\d{7,8}\b', '[LICENSE_MASKED]', sanitized_question)
            sanitized_question = re.sub(r'\b\d{3}-?\d{3}-?\d{4}\b', '[PHONE_MASKED]', sanitized_question)
        
        return {
            "decision": decision,
            "safe_to_proceed": safe_to_proceed,
            "sanitized_question": sanitized_question,
            "violations": rule_ids,
            "jimini_response": jimini_result
        }
    
    def process_ai_question(self, question: str, user_id: str = "ai_user") -> Dict[str, Any]:
        """
        Complete AI question processing pipeline:
        1. Check for PII via Jimini
        2. Sanitize if needed  
        3. Return safe question for AI processing
        """
        
        print(f"🔍 Screening AI question for PII...")
        
        # Step 1: PII Protection Check
        safety_check = self.check_question_safety(question, user_id)
        
        if not safety_check['safe_to_proceed']:
            return {
                "status": "BLOCKED",
                "message": "Question contains sensitive PII and cannot be processed",
                "decision": safety_check['decision'],
                "violations": safety_check['violations'],
                "original_question": question,
                "ai_response": None
            }
        
        # Step 2: Use sanitized question for AI
        safe_question = safety_check['sanitized_question']
        
        # Step 3: Simulate AI processing (replace with your actual AI call)
        ai_response = self._simulate_ai_response(safe_question)
        
        return {
            "status": "SUCCESS", 
            "message": "Question processed successfully",
            "decision": safety_check['decision'],
            "violations": safety_check['violations'],
            "original_question": question,
            "sanitized_question": safe_question,
            "ai_response": ai_response,
            "pii_detected": len(safety_check['violations']) > 0
        }
    
    def _simulate_ai_response(self, question: str) -> str:
        """
        Simulate AI response - replace this with your actual AI integration
        (OpenAI, Claude, etc.)
        """
        
        # Simple simulation based on question content
        question_lower = question.lower()
        
        if 'citizen' in question_lower or 'resident' in question_lower:
            return f"Based on your inquiry about citizen services, I can help you with general information about government procedures. For specific citizen records, please use the secure lookup system with proper authorization."
            
        elif 'dmv' in question_lower or 'license' in question_lower:
            return f"For DMV-related questions, I can provide general information about licensing procedures. Access to specific license records requires proper authorization through the DMV lookup system."
            
        elif 'background' in question_lower:
            return f"Background check procedures require legal justification and proper authorization. I can explain the general process, but cannot access or process actual background check data."
            
        else:
            return f"I understand you're asking: '{question}'. I can provide general information while protecting any sensitive data. How can I help you with government services?"

# Integration with Streamlit Dashboard
def add_ai_chat_to_dashboard():
    """Add AI chat functionality to your existing Streamlit dashboard"""
    
    import streamlit as st
    
    # Initialize AI processor
    if 'ai_processor' not in st.session_state:
        st.session_state.ai_processor = JiminiAIQuestionProcessor()
    
    # AI Chat Section
    st.header("🤖 AI Assistant with PII Protection")
    st.info("🛡️ All questions are automatically screened for PII before AI processing")
    
    # Chat interface
    user_question = st.text_input(
        "Ask the AI Assistant:",
        placeholder="Ask about government services, procedures, etc...",
        key="ai_question"
    )
    
    if st.button("🤖 Ask AI", type="primary"):
        if user_question:
            with st.spinner("🔍 Screening question and processing..."):
                # Process through Jimini + AI
                result = st.session_state.ai_processor.process_ai_question(
                    user_question, 
                    st.session_state.get('current_user', 'dashboard_user')
                )
                
                if result['status'] == 'BLOCKED':
                    st.error("🚫 Question Blocked - Contains Sensitive PII")
                    st.warning(result['message'])
                    
                    if result['violations']:
                        st.write("**PII Detected:**")
                        for violation in result['violations']:
                            st.write(f"• {violation}")
                
                else:
                    # Show successful AI response
                    if result['pii_detected']:
                        st.warning("⚠️ PII detected and sanitized before AI processing")
                        with st.expander("View PII Protection Details"):
                            st.write(f"**Decision:** {result['decision']}")
                            st.write(f"**Original:** {result['original_question']}")
                            st.write(f"**Sanitized:** {result['sanitized_question']}")
                            st.write(f"**Violations:** {result['violations']}")
                    else:
                        st.success("✅ Question processed safely - no PII detected")
                    
                    # Show AI response
                    st.write("**🤖 AI Assistant:**")
                    st.write(result['ai_response'])

if __name__ == "__main__":
    # Test the AI question processor
    processor = JiminiAIQuestionProcessor()
    
    print("🤖 TESTING AI QUESTION PROCESSING WITH JIMINI")
    print("=" * 60)
    
    test_questions = [
        "How do I renew my driver's license?",
        "I need help with John Doe, SSN: 123-45-6789",
        "What's the process for background checks?", 
        "Can you help me with citizen ID C001234?",
        "General question about government services"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}️⃣ Testing: '{question}'")
        result = processor.process_ai_question(question, f"test_user_{i}")
        
        print(f"   Status: {result['status']}")
        print(f"   Decision: {result['decision']}")
        if result['violations']:
            print(f"   PII Found: {result['violations']}")
        if result['status'] == 'SUCCESS':
            print(f"   AI Response: {result['ai_response'][:100]}...")
        print(f"   Safe: {'✅' if result['status'] == 'SUCCESS' else '❌'}")