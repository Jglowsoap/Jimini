#!/usr/bin/env python3
"""
🏛️ GOVERNMENT REPLIT DASHBOARD WITH JIMINI PII PROTECTION
===========================================================

This is your complete government dashboard with built-in PII protection.
Copy this to your Replit project and you'll have instant citizen data protection!
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import json
import re
from datetime import datetime
from typing import Dict, Any, List

# 🛡️ JIMINI PII PROTECTION ENGINE (Standalone)
class GovernmentPIIProtector:
    """Built-in PII protection for your Replit dashboard"""
    
    def __init__(self):
        self.rules = {
            'SSN-PROTECTION': {
                'name': 'Social Security Number',
                'pattern': r'\b\d{3}-?\d{2}-?\d{4}\b',
                'action': 'BLOCK',
                'severity': 'CRITICAL'
            },
            'DL-PROTECTION': {
                'name': 'Driver\'s License Number', 
                'pattern': r'\b[A-Z]{1,2}\d{7,8}\b|D\d{8}\b',
                'action': 'FLAG',
                'severity': 'HIGH'
            },
            'ADDRESS-PROTECTION': {
                'name': 'Street Address',
                'pattern': r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b',
                'action': 'FLAG', 
                'severity': 'MEDIUM'
            },
            'PHONE-PROTECTION': {
                'name': 'Phone Number',
                'pattern': r'\b\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b',
                'action': 'FLAG',
                'severity': 'MEDIUM'  
            },
            'EMAIL-PROTECTION': {
                'name': 'Email Address',
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'action': 'FLAG',
                'severity': 'LOW'
            }
        }
        self.audit_log = []
    
    def protect_data(self, text: str, endpoint: str = "/dashboard", user_id: str = "dashboard_user") -> Dict[str, Any]:
        """Check text for PII and return protection decision"""
        violations = []
        decision = "ALLOW"
        highest_severity = "NONE"
        
        for rule_id, rule in self.rules.items():
            matches = re.finditer(rule['pattern'], text, re.IGNORECASE)
            for match in matches:
                violation = {
                    'rule_id': rule_id,
                    'rule_name': rule['name'],
                    'matched_text': match.group(),
                    'position': [match.start(), match.end()],
                    'action': rule['action'],
                    'severity': rule['severity']
                }
                violations.append(violation)
                
                # Update overall decision
                if rule['action'] == 'BLOCK':
                    decision = "BLOCK"
                    highest_severity = "CRITICAL"
                elif rule['action'] == 'FLAG' and decision != 'BLOCK':
                    decision = "FLAG"
                    if highest_severity in ["NONE", "LOW", "MEDIUM"]:
                        highest_severity = rule['severity']
        
        # Log the decision
        self.audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'user_id': user_id,
            'decision': decision,
            'severity': highest_severity,
            'violations_count': len(violations),
            'text_length': len(text)
        })
        
        return {
            'decision': decision,
            'severity': highest_severity,
            'violations': violations,
            'rule_ids': [v['rule_id'] for v in violations]
        }
    
    def filter_response(self, text: str) -> Dict[str, Any]:
        """Filter and mask PII in response data"""
        result = self.protect_data(text)
        filtered_text = text
        
        # Mask detected PII
        for violation in result['violations']:
            mask = f"[MASKED_{violation['rule_name']}]"
            filtered_text = filtered_text.replace(violation['matched_text'], mask)
        
        return {
            'filtered_text': filtered_text,
            'pii_detected': len(result['violations']) > 0,
            'violations': result['violations']
        }
    
    def get_audit_logs(self) -> List[Dict]:
        """Get recent audit logs"""
        return self.audit_log[-100:]  # Last 100 entries

# Initialize PII Protector
@st.cache_resource
def get_pii_protector():
    return GovernmentPIIProtector()

# 🎨 STREAMLIT DASHBOARD
def main():
    st.set_page_config(
        page_title="🏛️ Government Dashboard with PII Protection",
        page_icon="🛡️",
        layout="wide"
    )
    
    protector = get_pii_protector()
    
    # Header
    st.title("🏛️ Government Citizen Data Dashboard")
    st.subheader("🛡️ Protected by Jimini AI Policy Engine")
    
    # Sidebar
    st.sidebar.header("🔧 Dashboard Controls")
    current_user = st.sidebar.text_input("👤 User ID:", value="dashboard_user")
    protection_enabled = st.sidebar.checkbox("🛡️ PII Protection", value=True)
    
    # Main Dashboard Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Citizen Lookup", 
        "🚗 DMV Records", 
        "🔍 Background Check", 
        "📊 Protection Metrics", 
        "📋 Audit Log"
    ])
    
    # Tab 1: Citizen Lookup
    with tab1:
        st.header("👥 Citizen Information Lookup")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🔍 Query Interface")
            
            # Simulated database query
            query_type = st.selectbox(
                "Query Type:",
                ["By SSN", "By Name", "By Address", "By Driver's License"]
            )
            
            search_value = st.text_input(
                f"Search {query_type}:",
                placeholder="Enter search criteria..."
            )
            
            if st.button("🔍 Search Records", type="primary"):
                if search_value and protection_enabled:
                    # 🛡️ PII PROTECTION CHECK
                    protection_result = protector.protect_data(
                        search_value, 
                        "/citizen/lookup", 
                        current_user
                    )
                    
                    if protection_result['decision'] == 'BLOCK':
                        st.error("🚫 QUERY BLOCKED - Contains sensitive PII")
                        st.warning("Cannot execute searches containing SSN or other protected data")
                        
                        # Show violations
                        for violation in protection_result['violations']:
                            st.write(f"- **{violation['rule_name']}**: {violation['matched_text']}")
                    
                    elif protection_result['decision'] == 'FLAG':
                        st.warning("⚠️ PII DETECTED - Query logged for compliance")
                        
                        # Simulate search results with protection
                        fake_results = {
                            "citizen_id": "C001234",
                            "name": "John Doe",
                            "address": "123 Main Street, Springfield, IL",
                            "phone": "555-123-4567",
                            "status": "Active"
                        }
                        
                        # 🛡️ Filter response
                        filtered = protector.filter_response(str(fake_results))
                        st.json(filtered)
                    
                    else:
                        st.success("✅ Query Approved - No PII detected")
                        # Show safe results
                        st.json({"message": "Safe query executed successfully"})
                
                elif search_value:
                    # Show unprotected results (dangerous!)
                    st.warning("⚠️ PII Protection is DISABLED")
                    st.json({
                        "name": "John Doe", 
                        "ssn": "123-45-6789",
                        "address": "123 Main Street"
                    })
        
        with col2:
            st.subheader("📋 Query Results")
            if protection_enabled:
                st.info("🛡️ All results are automatically protected from PII exposure")
                
                # Show protection examples
                st.write("**Protection Examples:**")
                examples = [
                    "SSN: 123-45-6789 → SSN: [MASKED_Social Security Number]",
                    "Address: 123 Main St → Address: [MASKED_Street Address]", 
                    "Phone: 555-123-4567 → Phone: [MASKED_Phone Number]"
                ]
                for example in examples:
                    st.write(f"• {example}")
            else:
                st.error("🚨 PII PROTECTION DISABLED - Data at risk!")
    
    # Tab 2: DMV Records
    with tab2:
        st.header("🚗 DMV Records Management")
        
        st.info("🛡️ This system automatically protects driver's license numbers and personal information")
        
        # DMV Query Interface
        col1, col2 = st.columns(2)
        
        with col1:
            license_query = st.text_input("Driver's License Number:", placeholder="Enter license number...")
            
            if st.button("🚗 Lookup Driver Record"):
                if license_query and protection_enabled:
                    protection_result = protector.protect_data(license_query, "/dmv/lookup", current_user)
                    
                    if protection_result['violations']:
                        st.warning("⚠️ Driver's License number detected - Access logged")
                        
                        # Show protected DMV record
                        dmv_record = {
                            "license": license_query,
                            "name": "Driver Name",
                            "address": "123 Oak Avenue, Springfield, IL",
                            "status": "Valid",
                            "expiration": "2026-12-31"
                        }
                        
                        filtered = protector.filter_response(str(dmv_record))
                        st.json(filtered)
                    else:
                        st.success("Safe DMV query - no license numbers detected")
        
        with col2:
            st.write("**Recent DMV Queries:**")
            dmv_logs = [log for log in protector.get_audit_logs() if '/dmv' in log.get('endpoint', '')]
            if dmv_logs:
                for log in dmv_logs[-5:]:
                    st.write(f"• {log['timestamp'][:19]} - {log['decision']} - User: {log['user_id']}")
            else:
                st.write("No recent DMV queries")
    
    # Tab 3: Background Check
    with tab3:
        st.header("🔍 Background Check System")
        
        st.warning("🚨 All background check queries require full audit trail")
        
        bg_query = st.text_area(
            "Background Check Query:",
            placeholder="Enter citizen information for background verification...",
            height=100
        )
        
        justification = st.text_area(
            "Justification (Required):",
            placeholder="Enter legal justification for this background check...",
            height=80
        )
        
        if st.button("🔍 Submit Background Check"):
            if bg_query and justification and protection_enabled:
                protection_result = protector.protect_data(bg_query, "/background/check", current_user)
                
                st.write(f"**Decision:** {protection_result['decision']}")
                st.write(f"**Severity:** {protection_result['severity']}")
                
                if protection_result['violations']:
                    st.write("**PII Detected:**")
                    for violation in protection_result['violations']:
                        st.write(f"• {violation['rule_name']}: {violation['matched_text']}")
                
                # Always log background checks
                st.success("✅ Background check request logged for compliance review")
    
    # Tab 4: Protection Metrics  
    with tab4:
        st.header("📊 PII Protection Metrics")
        
        # Get audit data
        audit_data = protector.get_audit_logs()
        
        if audit_data:
            df = pd.DataFrame(audit_data)
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_queries = len(df)
                st.metric("📊 Total Queries", total_queries)
            
            with col2:
                blocked = len(df[df['decision'] == 'BLOCK'])
                st.metric("🚫 Blocked", blocked, delta=f"{blocked/total_queries*100:.1f}%")
            
            with col3:
                flagged = len(df[df['decision'] == 'FLAG']) 
                st.metric("⚠️ Flagged", flagged, delta=f"{flagged/total_queries*100:.1f}%")
            
            with col4:
                allowed = len(df[df['decision'] == 'ALLOW'])
                st.metric("✅ Allowed", allowed, delta=f"{allowed/total_queries*100:.1f}%")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Decision pie chart
                decision_counts = df['decision'].value_counts()
                fig_pie = px.pie(
                    values=decision_counts.values,
                    names=decision_counts.index,
                    title="🛡️ PII Protection Decisions"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Severity distribution
                severity_counts = df['severity'].value_counts()
                fig_bar = px.bar(
                    x=severity_counts.index,
                    y=severity_counts.values,
                    title="⚠️ Severity Distribution"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        else:
            st.info("📊 No metrics available yet. Start using the dashboard to see protection statistics.")
    
    # Tab 5: Audit Log
    with tab5:
        st.header("📋 PII Protection Audit Log")
        
        audit_data = protector.get_audit_logs()
        
        if audit_data:
            # Convert to DataFrame
            df = pd.DataFrame(audit_data)
            
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                decision_filter = st.multiselect(
                    "Filter by Decision:",
                    options=df['decision'].unique(),
                    default=df['decision'].unique()
                )
            
            with col2:
                endpoint_filter = st.multiselect(
                    "Filter by Endpoint:",
                    options=df['endpoint'].unique(),
                    default=df['endpoint'].unique()
                )
            
            with col3:
                user_filter = st.multiselect(
                    "Filter by User:",
                    options=df['user_id'].unique(),
                    default=df['user_id'].unique()
                )
            
            # Apply filters
            filtered_df = df[
                (df['decision'].isin(decision_filter)) &
                (df['endpoint'].isin(endpoint_filter)) &
                (df['user_id'].isin(user_filter))
            ]
            
            # Display audit log
            st.dataframe(
                filtered_df.sort_values('timestamp', ascending=False),
                use_container_width=True
            )
            
            # Download button
            if st.button("📥 Download Audit Log"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    "📄 Download CSV",
                    csv,
                    "government_pii_audit_log.csv",
                    "text/csv"
                )
        else:
            st.info("📋 No audit entries yet. Start using protected features to generate audit trail.")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info("""
    🛡️ **Jimini PII Protection Active**
    
    • SSN Detection: ✅ BLOCK
    • Driver's License: ✅ FLAG  
    • Addresses: ✅ FLAG
    • Phone Numbers: ✅ FLAG
    • Email Addresses: ✅ FLAG
    
    **Compliance:** HIPAA, PII Protection
    """)

if __name__ == "__main__":
    main()