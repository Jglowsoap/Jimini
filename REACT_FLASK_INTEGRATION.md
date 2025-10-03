# 🎯 **REACT/FLASK DASHBOARD INTEGRATION GUIDE**

## 🚀 **Step 1: Choose Your Flask Backend Option**

### **🔧 Option A: Simple Embedded Rules (Fastest Setup)**
```python
# Use flask_pii_protection.py - Rules are coded in Python
# No external files needed, rules are embedded in the code
from flask_pii_protection import protector, app as pii_app
```

### **🔧 Option B: Dynamic Rule Management (Recommended)**
```python
# Use flask_advanced_rules.py - Rules come from YAML files + API management
# Rules can be updated without redeploying your app
from flask_advanced_rules import AdvancedPIIProtector, app as advanced_app

# Rules loaded from: government_rules.yaml (or any YAML/JSON file)
# Can be managed via React UI or API calls
```

### **Add to your existing Flask app:**

```python
# Option 1: Use as blueprint
your_app.register_blueprint(pii_app, url_prefix='/pii')

# Option 2: Copy the routes to your existing app
# (Copy the @app.route functions from flask_pii_protection.py)
```

### **Or run as separate microservice:**

```bash
# Terminal 1: Start PII Protection Service
cd /your/project
python flask_pii_protection.py
# Runs on http://localhost:5000

# Terminal 2: Start your main Flask app  
cd /your/project
python your_main_app.py
# Runs on http://localhost:3001 (or your port)
```

## ⚛️ **Step 2: React Frontend Integration**

### **Install dependencies:**

```bash
npm install axios
npm install -D tailwindcss  # For styling (optional)
```

### **Copy React components:**

```javascript
// Copy the components from react_components.jsx to your React app

// Example App.js
import React from 'react';
import { GovernmentDashboard } from './components/GovernmentDashboard';
import './App.css';

function App() {
  return (
    <div className="App">
      <GovernmentDashboard />
    </div>
  );
}

export default App;
```

## 🛡️ **Step 3: Quick Integration Examples**

### **1. Protect any input field:**

```jsx
import { ProtectedInput } from './components/GovernmentDashboard';

function MyForm() {
  const [searchQuery, setSearchQuery] = useState('');
  const [piiDetected, setPiiDetected] = useState(false);

  const handlePIIDetected = (decision, violations) => {
    setPiiDetected(decision === 'BLOCK');
    if (decision === 'BLOCK') {
      alert('Cannot submit form - contains sensitive PII');
    }
  };

  return (
    <form>
      <ProtectedInput
        placeholder="Enter search criteria..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        endpoint="/your/endpoint"
        onPIIDetected={handlePIIDetected}
        userId="current_user_id"
      />
      
      <button 
        type="submit" 
        disabled={piiDetected}
        className={piiDetected ? 'opacity-50 cursor-not-allowed' : ''}
      >
        Submit
      </button>
    </form>
  );
}
```

### **2. Protect API responses:**

```jsx
import { usePIIProtection } from './components/GovernmentDashboard';

function CitizenDataDisplay({ citizenData }) {
  const [maskedData, setMaskedData] = useState(null);
  const { maskPII } = usePIIProtection();

  useEffect(() => {
    const protectData = async () => {
      const result = await maskPII(JSON.stringify(citizenData));
      if (result.pii_detected) {
        setMaskedData(result.masked_text);
      } else {
        setMaskedData(JSON.stringify(citizenData, null, 2));
      }
    };

    protectData();
  }, [citizenData]);

  return (
    <div>
      {maskedData && (
        <pre className="bg-gray-100 p-4 rounded">
          {maskedData}
        </pre>
      )}
    </div>
  );
}
```

### **3. Add to existing forms:**

```jsx
// Before submitting any form
const handleSubmit = async (formData) => {
  const { checkPII } = usePIIProtection();
  
  // Check all form fields for PII
  const formText = Object.values(formData).join(' ');
  const protection = await checkPII(formText, '/form/submit', userId);
  
  if (protection.decision === 'BLOCK') {
    alert('Form contains sensitive PII and cannot be submitted');
    return;
  }
  
  if (protection.decision === 'FLAG') {
    const confirm = window.confirm('PII detected. This submission will be logged. Continue?');
    if (!confirm) return;
  }
  
  // Safe to submit
  submitForm(formData);
};
```

## 🔧 **Step 4: Backend API Endpoints**

### **🛡️ PII Protection APIs (Both Options):**
- `POST /api/pii/check` - Check text for PII
- `POST /api/pii/mask` - Mask PII in text

### **🏛️ Protected Government APIs (Both Options):**  
- `POST /api/citizen/lookup` - Protected citizen search
- `POST /api/dmv/lookup` - Protected DMV records
- `POST /api/background/check` - Audited background checks

### **📊 Monitoring APIs (Both Options):**
- `GET /api/metrics` - PII protection statistics
- `GET /api/audit/logs` - Compliance audit logs
- `GET /api/health` - Service health check

### **🔧 Rule Management APIs (Advanced Option Only):**
- `GET /api/rules` - List all rules (enabled and disabled)
- `PUT /api/rules/<rule_id>` - Update specific rule
- `POST /api/rules/<rule_id>/toggle` - Enable/disable rule
- `POST /api/rules` - Add new custom rule
- `POST /api/rules/reload` - Reload rules from YAML file

## 📋 **Rule Sources Explained:**

### **Simple Version (`flask_pii_protection.py`):**
```python
# Rules are embedded in Python code
self.rules = {
    'SSN-PROTECTION': {
        'pattern': r'\b\d{3}-?\d{2}-?\d{4}\b',
        'action': 'BLOCK'
    }
    # ... more rules
}
```
✅ **Pros:** Simple, no external dependencies  
❌ **Cons:** Must redeploy to change rules

### **Advanced Version (`flask_advanced_rules.py`):**
```yaml
# Rules come from government_rules.yaml file
rules:
  - id: SSN-PROTECTION
    pattern: '\b\d{3}-?\d{2}-?\d{4}\b'
    action: block
    enabled: true
```
✅ **Pros:** Update rules without redeploying, React UI management  
✅ **Pros:** Enable/disable rules dynamically  
❌ **Cons:** Requires YAML file management

## 📊 **Step 5: Test Your Protection**

### **Test in your React app:**

1. **Go to Citizen Lookup tab**
2. **Type:** `"John Doe SSN: 123-45-6789"` → Should be **BLOCKED** 🚫
3. **Type:** `"John Doe"` → Should be **ALLOWED** ✅  
4. **Type:** `"Address: 123 Main Street"` → Should be **FLAGGED** ⚠️

### **Test API directly:**

```bash
# Test PII check
curl -X POST http://localhost:5000/api/pii/check \
  -H "Content-Type: application/json" \
  -d '{"text": "SSN: 123-45-6789", "endpoint": "/test", "user_id": "test_user"}'

# Should return: {"status": "success", "protection_result": {"decision": "BLOCK", ...}}
```

## 🏛️ **Step 6: Government-Specific Features**

### **Audit Requirements:**
- All PII access is automatically logged
- Background checks require justification
- Supervisor notifications for cross-system access
- Downloadable compliance reports

### **Protection Rules Active:**
- ✅ **SSN Detection** → **BLOCK** (Critical)
- ✅ **Driver's License** → **FLAG** (High)  
- ✅ **Street Addresses** → **FLAG** (Medium)
- ✅ **Phone Numbers** → **FLAG** (Medium)
- ✅ **Email Addresses** → **FLAG** (Low)

### **Compliance Features:**
- **HIPAA Protection:** Medical data detection
- **PII Masking:** Automatic data redaction
- **Audit Trail:** Tamper-evident logging
- **User Tracking:** Individual accountability

## 🚀 **Step 7: Deployment Options**

### **Option 1: Integrated (Recommended)**
```bash
# Add PII protection routes to your existing Flask app
# Copy the functions from flask_pii_protection.py
# No separate service needed
```

### **Option 2: Microservice**
```bash
# Run PII protection as separate service
# Your React app calls both services
# Main app: http://localhost:3000
# PII service: http://localhost:5000
```

### **Option 3: Replit Deployment**
```bash
# Copy files to your Replit project
# Install: pip install flask flask-cors
# Run: python flask_pii_protection.py
# Access via your Replit URL
```

## 📱 **Step 8: Mobile/Responsive Design**

The React components use Tailwind CSS classes for responsive design:

```jsx
// The components automatically adapt to mobile
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* Responsive metrics grid */}
</div>

<div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
  {/* Responsive navigation */}
</div>
```

---

## 🎯 **You're Ready!**

Your React/Flask dashboard now has:

- ✅ **Real-time PII detection** in all input fields
- ✅ **Automatic response filtering** for safe data display
- ✅ **Government compliance** with audit trails
- ✅ **Professional UI components** ready for production
- ✅ **API protection** for all backend endpoints

**Start testing with your real government data patterns!**

### **Quick Start Commands:**

```bash
# Backend
python flask_pii_protection.py

# Frontend  
npm start

# Test
curl -X POST http://localhost:5000/api/pii/check -d '{"text":"SSN: 123-45-6789"}'
```

🏛️ **Your citizen data is now AI-protected!**