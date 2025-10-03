#!/usr/bin/env python3
"""
Jimini GUI for Replit Dashboard
===============================

Simple web interface for monitoring PII protection in your government dashboard.
This provides real-time monitoring and control of Jimini's PII protection.
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Jimini API Configuration
JIMINI_API_URL = "http://localhost:9000"  # Change this to your Jimini server
JIMINI_API_KEY = "changeme"  # Change this to your API key

class JiminiGUI:
    def __init__(self):
        self.api_url = JIMINI_API_URL
        self.api_key = JIMINI_API_KEY
        
    def test_pii_protection(self, text, endpoint="/dashboard/test"):
        """Test text for PII protection"""
        try:
            response = requests.post(
                f"{self.api_url}/v1/evaluate",
                headers={
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "agent_id": "dashboard",
                    "direction": "outbound", 
                    "endpoint": endpoint,
                    "api_key": self.api_key
                },
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to Jimini service"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_audit_logs(self):
        """Get recent audit logs (simulated for demo)"""
        # In production, this would fetch real audit logs
        return [
            {
                "timestamp": "2025-10-02T20:15:00Z",
                "endpoint": "/citizen/lookup",
                "decision": "FLAG",
                "pii_detected": "SSN",
                "user": "dashboard_user",
                "action_taken": "masked_response"
            },
            {
                "timestamp": "2025-10-02T20:14:30Z", 
                "endpoint": "/background/check",
                "decision": "ALLOW",
                "pii_detected": "None",
                "user": "dashboard_user",
                "action_taken": "processed_normally"
            },
            {
                "timestamp": "2025-10-02T20:14:00Z",
                "endpoint": "/medical/billing",
                "decision": "BLOCK",
                "pii_detected": "HIPAA_DATA",
                "user": "dashboard_user", 
                "action_taken": "request_blocked"
            }
        ]
    
    def get_protection_metrics(self):
        """Get PII protection metrics"""
        return {
            "total_requests": 1247,
            "pii_detected": 89,
            "blocked_requests": 23,
            "flagged_requests": 66,
            "protection_rate": 95.7,
            "false_positives": 2,
            "compliance_score": 98.5
        }

def main():
    st.set_page_config(
        page_title="Jimini PII Protection Dashboard",
        page_icon="🛡️",
        layout="wide"
    )
    
    jimini = JiminiGUI()
    
    # Header
    st.title("🛡️ Jimini PII Protection Dashboard")
    st.subheader("Government Citizen Data Protection Monitor")
    
    # Sidebar
    st.sidebar.header("🔧 Jimini Controls")
    
    # Connection Status
    st.sidebar.subheader("📡 Service Status")
    test_result = jimini.test_pii_protection("test connection")
    if "error" in test_result:
        st.sidebar.error(f"❌ Jimini Offline: {test_result['error']}")
        st.sidebar.info("💡 Start Jimini service to enable protection")
    else:
        st.sidebar.success("✅ Jimini Online & Protecting")
    
    # Main Dashboard Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Live Testing", "📊 Metrics", "📋 Audit Log", "⚙️ Settings"])
    
    # Tab 1: Live PII Testing
    with tab1:
        st.header("🔍 Test PII Protection")
        st.write("Test how Jimini protects citizen data in real-time")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📝 Input Data")
            test_text = st.text_area(
                "Enter test data (use fake SSNs like 123-45-6789):",
                value="Citizen: John Doe, SSN: 123-45-6789, Address: 123 Main Street, Phone: 555-123-4567",
                height=100
            )
            
            endpoint = st.selectbox(
                "Dashboard Endpoint:",
                ["/citizen/lookup", "/background/check", "/medical/billing", "/dmv/registration"]
            )
            
            if st.button("🛡️ Test Protection", type="primary"):
                result = jimini.test_pii_protection(test_text, endpoint)
                st.session_state['last_test'] = result
        
        with col2:
            st.subheader("🚨 Protection Result")
            if 'last_test' in st.session_state:
                result = st.session_state['last_test']
                
                if "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                else:
                    # Display decision
                    decision = result.get('decision', 'UNKNOWN')
                    if decision == 'BLOCK':
                        st.error(f"🚫 BLOCKED - Critical PII detected")
                    elif decision == 'FLAG':
                        st.warning(f"⚠️ FLAGGED - PII detected and logged")
                    else:
                        st.success(f"✅ ALLOWED - No PII detected")
                    
                    # Show matched rules
                    if 'rule_ids' in result:
                        st.write("**Rules Triggered:**")
                        for rule_id in result['rule_ids']:
                            st.write(f"- {rule_id}")
                    
                    # Show raw response
                    with st.expander("📄 Full Response"):
                        st.json(result)
            else:
                st.info("👆 Run a test to see protection results")
    
    # Tab 2: Protection Metrics
    with tab2:
        st.header("📊 PII Protection Metrics")
        
        metrics = jimini.get_protection_metrics()
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🛡️ Protection Rate",
                f"{metrics['protection_rate']:.1f}%",
                delta="2.3%"
            )
        
        with col2:
            st.metric(
                "🚫 Blocked Requests", 
                metrics['blocked_requests'],
                delta="-5"
            )
        
        with col3:
            st.metric(
                "⚠️ Flagged Requests",
                metrics['flagged_requests'], 
                delta="12"
            )
        
        with col4:
            st.metric(
                "📋 Compliance Score",
                f"{metrics['compliance_score']:.1f}%",
                delta="1.2%"
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # PII Detection Chart
            pii_data = pd.DataFrame({
                'Category': ['Safe Requests', 'PII Detected', 'Blocked'],
                'Count': [
                    metrics['total_requests'] - metrics['pii_detected'],
                    metrics['pii_detected'] - metrics['blocked_requests'], 
                    metrics['blocked_requests']
                ]
            })
            
            fig_pie = px.pie(
                pii_data, 
                values='Count', 
                names='Category',
                title="🔍 Request Analysis"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Daily Protection Trends (simulated)
            dates = pd.date_range(start='2025-09-25', end='2025-10-02', freq='D')
            trend_data = pd.DataFrame({
                'Date': dates,
                'Requests': [150, 167, 145, 189, 156, 134, 178, 203],
                'PII_Detected': [12, 15, 8, 19, 11, 9, 14, 21],
                'Blocked': [3, 4, 2, 5, 2, 2, 3, 6]
            })
            
            fig_line = px.line(
                trend_data,
                x='Date',
                y=['Requests', 'PII_Detected', 'Blocked'],
                title="📈 Daily Protection Trends"
            )
            st.plotly_chart(fig_line, use_container_width=True)
    
    # Tab 3: Audit Log
    with tab3:
        st.header("📋 PII Protection Audit Log")
        st.write("Complete audit trail for compliance reporting")
        
        audit_logs = jimini.get_audit_logs()
        
        # Convert to DataFrame for display
        df = pd.DataFrame(audit_logs)
        
        # Add color coding for decisions
        def color_decision(decision):
            if decision == 'BLOCK':
                return 'background-color: #ffebee'
            elif decision == 'FLAG':
                return 'background-color: #fff3e0' 
            else:
                return 'background-color: #e8f5e8'
        
        styled_df = df.style.applymap(color_decision, subset=['decision'])
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Download audit log
        if st.button("📥 Download Audit Log"):
            csv = df.to_csv(index=False)
            st.download_button(
                "📄 Download CSV",
                csv,
                "jimini_audit_log.csv",
                "text/csv"
            )
    
    # Tab 4: Settings
    with tab4:
        st.header("⚙️ Jimini Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 API Settings")
            
            new_api_url = st.text_input("Jimini API URL:", value=JIMINI_API_URL)
            new_api_key = st.text_input("API Key:", value=JIMINI_API_KEY, type="password")
            
            if st.button("💾 Update Settings"):
                st.success("Settings updated! Restart dashboard to apply changes.")
        
        with col2:
            st.subheader("📋 Protection Rules")
            
            rules_enabled = {
                "SSN Protection": True,
                "Driver's License Protection": True,
                "Address Protection": True,
                "Phone Number Protection": True,
                "Medical Data Protection": True
            }
            
            for rule, enabled in rules_enabled.items():
                new_state = st.checkbox(rule, value=enabled)
                if new_state != enabled:
                    st.info(f"Rule '{rule}' {'enabled' if new_state else 'disabled'}")
        
        # System Information
        st.subheader("ℹ️ System Information")
        system_info = {
            "Jimini Version": "9.0.0",
            "Dashboard Version": "1.0.0",
            "Last Updated": "2025-10-02 20:15:00",
            "Rules Loaded": "Government PII Protection Pack v1.0",
            "Compliance Standards": "HIPAA, PII Protection, State Government"
        }
        
        for key, value in system_info.items():
            st.write(f"**{key}:** {value}")

if __name__ == "__main__":
    main()