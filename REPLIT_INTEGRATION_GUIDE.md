# 🎯 Jimini Replit Dashboard Integration Guide

## 🚀 **Quick Start: Add PII Protection to Your Dashboard**

### **Option 1: Simple Function Calls (Easiest)**

```python
# Add this to your Replit dashboard
from replit_integration import JiminiMonitor, protect_citizen_record

# Initialize Jimini protection
jimini = JiminiMonitor(
    api_url="http://localhost:9000",  # Your Jimini server
    api_key="changeme"               # Your API key
)

# Protect citizen data before displaying
def display_citizen_info(citizen_id):
    # Get your citizen data (your existing code)
    citizen_data = get_citizen_from_database(citizen_id)
    
    # 🛡️ ADD THIS LINE - Protect the data
    protected_data = jimini.check_citizen_data(citizen_data)
    
    # Check if data was blocked
    if protected_data['decision'] == 'BLOCK':
        return "❌ Cannot display - sensitive PII detected"
    
    # Display the protected data
    return protected_data['redacted_data']
```

### **Option 2: Automatic Protection Decorator**

```python
from replit_integration import protect_pii, JiminiMonitor

# Initialize monitor
monitor = JiminiMonitor()

# 🛡️ ADD THIS DECORATOR to any function that returns citizen data
@protect_pii("/citizen/lookup", monitor)
def get_citizen_background_check(citizen_id):
    # Your existing code
    return {
        "name": "John Doe",
        "ssn": "123-45-6789",  # This will be automatically protected
        "status": "Clear"
    }
```

### **Option 3: Manual PII Checks**

```python
from replit_integration import quick_pii_check

# Before sending any data to your dashboard
def send_to_dashboard(data_string):
    # 🛡️ Quick PII check
    decision = quick_pii_check(data_string)
    
    if decision == "BLOCK":
        return "Data blocked - contains sensitive PII"
    elif decision == "FLAG":
        log_pii_access(data_string)  # Log the access
    
    return data_string  # Safe to display
```

## 🎨 **Full GUI Dashboard Setup**

### **1. Install Requirements in Replit**

Add to your `requirements.txt`:
```
streamlit
plotly
pandas
requests
```

### **2. Run Jimini Service**

In your Replit terminal:
```bash
# Start Jimini service
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000 &

# Verify it's running
curl http://localhost:9000/health
```

### **3. Launch GUI Dashboard**

```bash
# Run the Streamlit GUI
streamlit run jimini_gui_dashboard.py --server.port 8501
```

### **4. Access Your Dashboard**

- **GUI URL**: `https://your-repl-name.your-username.repl.co:8501`
- **API URL**: `https://your-repl-name.your-username.repl.co:9000`

## 🔧 **Integration Examples**

### **Example 1: DMV Dashboard Integration**

```python
from replit_integration import JiminiMonitor

jimini = JiminiMonitor()

def display_driver_record(license_number):
    # Get driver data from DMV database
    driver_data = {
        "name": "Jane Smith",
        "license": "D87654321",
        "address": "456 Oak Avenue, Springfield, IL 62701",
        "violations": ["Speeding 2023-05-15"]
    }
    
    # 🛡️ Protect before displaying
    result = jimini.check_citizen_data(driver_data)
    
    if result['decision'] == 'BLOCK':
        return {"error": "Cannot display record - sensitive data detected"}
    
    return result['redacted_data']
```

### **Example 2: Background Check Integration**

```python
def process_background_check(ssn, name):
    # Create the query data
    query_data = f"Background check for {name}, SSN: {ssn}"
    
    # 🛡️ Check if query contains PII that should be blocked
    protection = jimini.protect_data(query_data, "/background/check")
    
    if protection['decision'] == 'BLOCK':
        return {
            "status": "BLOCKED",
            "reason": "Query contains sensitive PII",
            "contact_supervisor": True
        }
    
    # Proceed with background check...
    return run_background_check(ssn, name)
```

### **Example 3: Medical Billing Dashboard**

```python
def display_patient_billing(patient_id):
    billing_info = get_patient_billing(patient_id)
    
    # Convert to text for PII scanning
    billing_text = f"""
    Patient: {billing_info['name']}
    SSN: {billing_info['ssn']}
    Insurance: {billing_info['insurance_number']}
    Amount: ${billing_info['amount']}
    """
    
    # 🛡️ Medical data requires extra protection
    protection = jimini.protect_data(billing_text, "/medical/billing")
    
    if protection['decision'] == 'BLOCK':
        # Block access - HIPAA violation risk
        audit_log("MEDICAL_PII_BLOCKED", patient_id)
        return {"error": "Medical data access blocked - HIPAA protection"}
    
    elif protection['decision'] == 'FLAG':
        # Allow but log for compliance
        audit_log("MEDICAL_PII_FLAGGED", patient_id)
    
    return billing_info
```

## ⚡ **Real-Time Monitoring Setup**

### **Add to Your Dashboard's Main Loop**

```python
import time
from replit_integration import JiminiMonitor

jimini = JiminiMonitor()

def dashboard_middleware(request_data, endpoint):
    """Add this to every dashboard request"""
    
    # 🛡️ Check all outgoing data for PII
    protection_result = jimini.protect_data(
        str(request_data), 
        endpoint,
        user_id=get_current_user_id()
    )
    
    # Log the protection decision
    log_protection_decision(protection_result)
    
    # Block if necessary
    if protection_result['decision'] == 'BLOCK':
        raise SecurityError("PII protection blocked this request")
    
    return protection_result
```

## 📊 **Monitoring Dashboard URLs**

Once running, you'll have:

1. **🎨 Jimini GUI**: `http://localhost:8501`
   - Live PII testing
   - Protection metrics
   - Audit logs
   - Settings

2. **🔧 Jimini API**: `http://localhost:9000`
   - `/v1/evaluate` - PII protection
   - `/v1/metrics` - Statistics
   - `/health` - Service status

3. **📋 Your Dashboard**: Integration with your existing Replit app

## 🚨 **Government Compliance Features**

### **Automatic Audit Logging**

```python
# Every PII check is automatically logged to:
# - logs/audit.jsonl (tamper-evident chain)
# - Your compliance system (via webhook)

# Get audit report for compliance officer
def generate_compliance_report(start_date, end_date):
    return jimini.get_audit_logs(start_date, end_date)
```

### **HIPAA/PII Rules Active**

- ✅ SSN Detection & Blocking
- ✅ Driver's License Flagging  
- ✅ Address Masking
- ✅ Phone Number Protection
- ✅ Medical Data Blocking

## 🎯 **Next Steps**

1. **Copy** `replit_integration.py` to your Replit project
2. **Add** the protection calls to your dashboard functions
3. **Run** Jimini service in background
4. **Launch** the GUI dashboard
5. **Test** with your real (anonymized) data

**Need help?** The GUI dashboard has a "Live Testing" tab where you can test PII protection with your actual data patterns!

---

🛡️ **Your citizen data is now protected by Jimini's AI-powered PII detection!**