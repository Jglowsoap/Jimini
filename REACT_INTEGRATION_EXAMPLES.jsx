// React Integration Example for Jimini Platform
// ============================================
// This file shows how your React dashboard integrates with Jimini

import React, { useState, useCallback } from 'react';

// ===========================================================
// Option 1: Direct Integration with Jimini Platform
// ===========================================================

/**
 * Custom hook for direct Jimini Platform integration
 */
export const useJiminiDirect = () => {
  const JIMINI_API_URL = 'http://localhost:9000/v1/evaluate';
  const JIMINI_API_KEY = 'changeme'; // Change in production!

  const evaluateText = useCallback(async (text, endpoint = '/dashboard/default') => {
    try {
      const response = await fetch(JIMINI_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: JIMINI_API_KEY,
          agent_id: 'react_dashboard',
          text: text,
          direction: 'outbound',
          endpoint: endpoint,
        }),
      });

      if (!response.ok) {
        throw new Error(`Jimini API error: ${response.status}`);
      }

      const result = await response.json();
      
      return {
        decision: result.action.toUpperCase(), // 'ALLOW', 'FLAG', 'BLOCK'
        ruleIds: result.rule_ids || [],
        message: result.message,
        isBlocked: result.action === 'block',
        isFlagged: result.action === 'flag',
      };
    } catch (error) {
      console.error('Jimini evaluation failed:', error);
      // Fail-safe: allow on error but log it
      return {
        decision: 'ALLOW',
        ruleIds: [],
        message: 'Evaluation service unavailable',
        isBlocked: false,
        isFlagged: false,
        error: error.message,
      };
    }
  }, []);

  return { evaluateText };
};

// ===========================================================
// Option 2: Flask Gateway Integration (Recommended)
// ===========================================================

/**
 * Custom hook for Flask Gateway integration (includes enterprise features)
 */
export const useJiminiGateway = (userId = 'anonymous') => {
  const FLASK_API_URL = 'http://localhost:5001/api/jimini/evaluate';

  const evaluateText = useCallback(async (text, endpoint = '/dashboard/default') => {
    try {
      const response = await fetch(FLASK_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          user_id: userId,
          endpoint: endpoint,
          agent_id: 'react_dashboard',
        }),
      });

      if (!response.ok) {
        throw new Error(`Flask Gateway error: ${response.status}`);
      }

      const result = await response.json();
      
      return {
        decision: result.decision,
        ruleIds: result.rule_ids || [],
        message: result.message,
        isBlocked: result.decision === 'BLOCK',
        isFlagged: result.decision === 'FLAG',
        auditLogged: result.audit_logged,
        tamperProof: result.tamper_proof,
        enterpriseFeatures: result.jimini_version === 'enterprise',
      };
    } catch (error) {
      console.error('Flask Gateway evaluation failed:', error);
      return {
        decision: 'ALLOW',
        ruleIds: [],
        message: 'Gateway service unavailable',
        isBlocked: false,
        isFlagged: false,
        error: error.message,
      };
    }
  }, [userId]);

  return { evaluateText };
};

// ===========================================================
// Example Component: Protected Input Field
// ===========================================================

export const ProtectedInputField = ({ userId }) => {
  const [inputValue, setInputValue] = useState('');
  const [piiDetected, setPiiDetected] = useState(null);
  const [isChecking, setIsChecking] = useState(false);
  
  // Use Flask Gateway (or switch to useJiminiDirect for direct integration)
  const { evaluateText } = useJiminiGateway(userId);

  const handleInputChange = async (e) => {
    const newValue = e.target.value;
    setInputValue(newValue);

    // Real-time PII detection (debounce in production)
    if (newValue.trim().length > 3) {
      setIsChecking(true);
      const result = await evaluateText(newValue, '/dashboard/input');
      setPiiDetected(result);
      setIsChecking(false);
    } else {
      setPiiDetected(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Final check before submission
    const result = await evaluateText(inputValue, '/dashboard/submit');

    if (result.isBlocked) {
      alert(`❌ Cannot submit: ${result.message}\nBlocked by rules: ${result.ruleIds.join(', ')}`);
      return;
    }

    if (result.isFlagged) {
      const confirmed = window.confirm(
        `⚠️ Sensitive content detected!\nRules: ${result.ruleIds.join(', ')}\n\nDo you want to continue?`
      );
      if (!confirmed) return;
    }

    // Proceed with submission
    console.log('✅ Submitting:', inputValue);
    // ... your submission logic ...
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="protected-input-container">
        <label>
          Enter Data (PII Protected):
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            placeholder="Type here..."
            disabled={isChecking}
          />
        </label>

        {isChecking && <span className="checking">🔍 Checking for PII...</span>}

        {piiDetected && piiDetected.isBlocked && (
          <div className="alert alert-danger">
            ❌ <strong>BLOCKED:</strong> {piiDetected.message}
            <br />
            Rules: {piiDetected.ruleIds.join(', ')}
          </div>
        )}

        {piiDetected && piiDetected.isFlagged && !piiDetected.isBlocked && (
          <div className="alert alert-warning">
            ⚠️ <strong>FLAGGED:</strong> Sensitive content detected
            <br />
            Rules: {piiDetected.ruleIds.join(', ')}
          </div>
        )}

        {piiDetected && !piiDetected.isBlocked && !piiDetected.isFlagged && (
          <div className="alert alert-success">
            ✅ <strong>SAFE:</strong> No PII detected
          </div>
        )}

        <button type="submit" disabled={piiDetected?.isBlocked || isChecking}>
          Submit
        </button>
      </div>
    </form>
  );
};

// ===========================================================
// Example Component: Government Citizen Lookup
// ===========================================================

export const CitizenLookup = ({ userId }) => {
  const [query, setQuery] = useState('');
  const [justification, setJustification] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleLookup = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // First check the query with Jimini
      const piiCheck = await fetch('http://localhost:5001/api/jimini/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: query,
          user_id: userId,
          endpoint: '/government/citizen/lookup',
        }),
      });

      const piiResult = await piiCheck.json();

      if (piiResult.decision === 'BLOCK') {
        alert('❌ Query contains blocked content. Cannot proceed.');
        setLoading(false);
        return;
      }

      // Proceed with actual lookup
      const lookupResponse = await fetch('http://localhost:5001/api/government/citizen/lookup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          user_id: userId,
          justification: justification,
        }),
      });

      const lookupResult = await lookupResponse.json();
      setResult(lookupResult);
    } catch (error) {
      console.error('Lookup failed:', error);
      setResult({ status: 'error', message: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="citizen-lookup">
      <h2>🏛️ Citizen Lookup (PII Protected)</h2>
      
      <form onSubmit={handleLookup}>
        <div className="form-group">
          <label>Search Query:</label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter citizen name or ID"
            required
          />
        </div>

        <div className="form-group">
          <label>Legal Justification:</label>
          <textarea
            value={justification}
            onChange={(e) => setJustification(e.target.value)}
            placeholder="Reason for accessing citizen records..."
            required
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? '🔍 Searching...' : '🔍 Search'}
        </button>
      </form>

      {result && (
        <div className={`result ${result.status}`}>
          {result.status === 'blocked' && (
            <div className="alert alert-danger">
              ❌ <strong>BLOCKED:</strong> {result.message}
              <p>Jimini detected sensitive content in your query.</p>
            </div>
          )}

          {result.status === 'success' && (
            <div className="citizen-data">
              <h3>✅ Citizen Found</h3>
              <pre>{JSON.stringify(result.citizen_data, null, 2)}</pre>
              <p className="audit-note">
                🔒 This access has been logged and audited.
              </p>
            </div>
          )}

          {result.status === 'not_found' && (
            <div className="alert alert-warning">
              ⚠️ Citizen not found in database
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ===========================================================
// Example: App Integration
// ===========================================================

export default function App() {
  const [userId] = useState('officer_12345'); // Get from your auth system

  return (
    <div className="app">
      <h1>🏛️ Government Dashboard with Jimini Protection</h1>
      
      <div className="dashboard-section">
        <h2>Protected Input Example</h2>
        <ProtectedInputField userId={userId} />
      </div>

      <div className="dashboard-section">
        <h2>Citizen Lookup Example</h2>
        <CitizenLookup userId={userId} />
      </div>

      <div className="dashboard-section">
        <h2>Integration Status</h2>
        <IntegrationStatus />
      </div>
    </div>
  );
}

// ===========================================================
// Integration Status Component
// ===========================================================

const IntegrationStatus = () => {
  const [status, setStatus] = useState(null);

  const checkStatus = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/jimini/health');
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      setStatus({ status: 'error', error: error.message });
    }
  };

  React.useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  if (!status) return <div>Loading status...</div>;

  return (
    <div className="integration-status">
      <h3>Jimini Integration Status</h3>
      <ul>
        <li>
          Status: {status.status === 'healthy' ? '✅ Healthy' : '❌ Unhealthy'}
        </li>
        <li>
          Jimini Connected: {status.jimini_connected ? '✅ Yes' : '❌ No'}
        </li>
        <li>
          Version: {status.version || 'Unknown'}
        </li>
        <li>
          Features: {status.features?.join(', ') || 'None'}
        </li>
      </ul>
    </div>
  );
};
