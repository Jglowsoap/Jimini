// React Components with Jimini PII Protection
// ==========================================

import React, { useState, useEffect } from 'react';
import axios from 'axios';

// API Base URL - adjust for your Flask backend
const API_BASE = 'http://localhost:5000/api';

// 🛡️ PII Protection Hook
const usePIIProtection = () => {
  const checkPII = async (text, endpoint = '/unknown', userId = 'user') => {
    try {
      const response = await axios.post(`${API_BASE}/pii/check`, {
        text,
        endpoint,
        user_id: userId
      });
      return response.data.protection_result;
    } catch (error) {
      console.error('PII check failed:', error);
      return { decision: 'ALLOW', violations: [] }; // Fail-safe
    }
  };

  const maskPII = async (text) => {
    try {
      const response = await axios.post(`${API_BASE}/pii/mask`, { text });
      return response.data.masked_result;
    } catch (error) {
      console.error('PII masking failed:', error);
      return { masked_text: text, pii_detected: false };
    }
  };

  return { checkPII, maskPII };
};

// 🛡️ Protected Input Component
const ProtectedInput = ({ 
  placeholder, 
  value, 
  onChange, 
  endpoint = '/input',
  onPIIDetected = () => {},
  className = '',
  userId = 'user'
}) => {
  const [piiStatus, setPIIStatus] = useState('safe');
  const [violations, setViolations] = useState([]);
  const { checkPII } = usePIIProtection();

  const handleChange = async (e) => {
    const inputValue = e.target.value;
    onChange(e);

    if (inputValue.length > 3) {
      const protection = await checkPII(inputValue, endpoint, userId);
      
      if (protection.decision === 'BLOCK') {
        setPIIStatus('blocked');
        setViolations(protection.violations);
        onPIIDetected('BLOCK', protection.violations);
      } else if (protection.decision === 'FLAG') {
        setPIIStatus('flagged');
        setViolations(protection.violations);
        onPIIDetected('FLAG', protection.violations);
      } else {
        setPIIStatus('safe');
        setViolations([]);
      }
    }
  };

  const getBorderColor = () => {
    switch (piiStatus) {
      case 'blocked': return 'border-red-500 bg-red-50';
      case 'flagged': return 'border-yellow-500 bg-yellow-50';
      default: return 'border-gray-300';
    }
  };

  return (
    <div className="relative">
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={handleChange}
        className={`w-full p-3 border rounded-lg ${getBorderColor()} ${className}`}
      />
      
      {piiStatus === 'blocked' && (
        <div className="absolute top-full left-0 mt-1 p-2 bg-red-100 border border-red-300 rounded text-red-700 text-sm">
          🚫 BLOCKED: Contains sensitive PII
          <ul className="mt-1">
            {violations.map((v, i) => (
              <li key={i}>• {v.rule_name}: {v.matched_text}</li>
            ))}
          </ul>
        </div>
      )}
      
      {piiStatus === 'flagged' && (
        <div className="absolute top-full left-0 mt-1 p-2 bg-yellow-100 border border-yellow-300 rounded text-yellow-700 text-sm">
          ⚠️ FLAGGED: PII detected and logged
          <ul className="mt-1">
            {violations.map((v, i) => (
              <li key={i}>• {v.rule_name}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// 👥 Citizen Lookup Component
const CitizenLookup = ({ userId = 'dashboard_user' }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [piiBlocked, setPIIBlocked] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/citizen/lookup`, {
        query,
        user_id: userId
      });

      if (response.data.status === 'blocked') {
        setPIIBlocked(true);
        setResults(response.data);
      } else {
        setPIIBlocked(false);
        setResults(response.data);
      }
    } catch (error) {
      console.error('Search failed:', error);
      setResults({ status: 'error', message: 'Search failed' });
    }
    setLoading(false);
  };

  const handlePIIDetected = (decision, violations) => {
    if (decision === 'BLOCK') {
      setPIIBlocked(true);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">👥 Citizen Lookup</h2>
      
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">Search Query:</label>
        <ProtectedInput
          placeholder="Enter citizen name or ID (do not enter SSN)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          endpoint="/citizen/lookup"
          onPIIDetected={handlePIIDetected}
          userId={userId}
          className="mb-2"
        />
        
        <button
          onClick={handleSearch}
          disabled={loading || piiBlocked}
          className={`px-4 py-2 rounded font-medium ${
            piiBlocked 
              ? 'bg-red-300 text-red-700 cursor-not-allowed' 
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
        >
          {loading ? '🔍 Searching...' : piiBlocked ? '🚫 Query Blocked' : '🔍 Search'}
        </button>
      </div>

      {results && (
        <div className="mt-4">
          {results.status === 'blocked' && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              <strong>🚫 Search Blocked</strong>
              <p>{results.message}</p>
              <div className="mt-2">
                <strong>PII Detected:</strong>
                <ul className="list-disc list-inside">
                  {results.protection_result.violations.map((v, i) => (
                    <li key={i}>{v.rule_name}: {v.matched_text}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {results.status === 'success' && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
              <strong>✅ Results Found</strong>
              {results.citizen_data && (
                <pre className="mt-2 text-sm">
                  {JSON.stringify(results.citizen_data, null, 2)}
                </pre>
              )}
              {results.masked_data && (
                <div className="mt-2">
                  <strong>🛡️ Protected Data:</strong>
                  <pre className="text-sm">{results.masked_data}</pre>
                </div>
              )}
            </div>
          )}

          {results.status === 'not_found' && (
            <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
              ℹ️ No citizen records found
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// 🚗 DMV Records Component
const DMVLookup = ({ userId = 'dmv_user' }) => {
  const [licenseNumber, setLicenseNumber] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleLookup = async () => {
    if (!licenseNumber.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/dmv/lookup`, {
        license_number: licenseNumber,
        user_id: userId
      });

      setResults(response.data);
    } catch (error) {
      console.error('DMV lookup failed:', error);
      setResults({ status: 'error', message: 'DMV lookup failed' });
    }
    setLoading(false);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">🚗 DMV Records</h2>
      
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">Driver's License Number:</label>
        <ProtectedInput
          placeholder="Enter driver's license number"
          value={licenseNumber}
          onChange={(e) => setLicenseNumber(e.target.value)}
          endpoint="/dmv/lookup"
          userId={userId}
          className="mb-2"
        />
        
        <button
          onClick={handleLookup}
          disabled={loading}
          className="px-4 py-2 bg-green-500 text-white rounded font-medium hover:bg-green-600 disabled:opacity-50"
        >
          {loading ? '🔍 Looking up...' : '🚗 Lookup Record'}
        </button>
      </div>

      {results && (
        <div className="mt-4">
          {results.status === 'success' && (
            <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded">
              <strong>✅ DMV Record Found</strong>
              {results.protection_applied && (
                <p className="text-sm mt-1">⚠️ Driver's license access logged for audit</p>
              )}
              <pre className="mt-2 text-sm">
                {JSON.stringify(results.dmv_record, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// 📊 Protection Metrics Component
const ProtectionMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get(`${API_BASE}/metrics`);
        setMetrics(response.data.metrics);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    };

    const fetchAuditLogs = async () => {
      try {
        const response = await axios.get(`${API_BASE}/audit/logs?limit=10`);
        setAuditLogs(response.data.logs);
      } catch (error) {
        console.error('Failed to fetch audit logs:', error);
      }
    };

    fetchMetrics();
    fetchAuditLogs();
    
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchMetrics();
      fetchAuditLogs();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  if (!metrics) {
    return <div className="p-6">Loading metrics...</div>;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">📊 PII Protection Metrics</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-100 p-4 rounded text-center">
          <div className="text-2xl font-bold text-blue-600">{metrics.total_requests}</div>
          <div className="text-sm text-blue-600">Total Requests</div>
        </div>
        
        <div className="bg-red-100 p-4 rounded text-center">
          <div className="text-2xl font-bold text-red-600">{metrics.blocked}</div>
          <div className="text-sm text-red-600">Blocked</div>
        </div>
        
        <div className="bg-yellow-100 p-4 rounded text-center">
          <div className="text-2xl font-bold text-yellow-600">{metrics.flagged}</div>
          <div className="text-sm text-yellow-600">Flagged</div>
        </div>
        
        <div className="bg-green-100 p-4 rounded text-center">
          <div className="text-2xl font-bold text-green-600">{metrics.protection_rate}%</div>
          <div className="text-sm text-green-600">Protection Rate</div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">📋 Recent Activity</h3>
        <div className="space-y-2">
          {auditLogs.slice(0, 5).map((log, index) => (
            <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
              <div>
                <span className="font-medium">{log.endpoint}</span>
                <span className="ml-2 text-sm text-gray-600">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  log.decision === 'BLOCK' ? 'bg-red-100 text-red-700' :
                  log.decision === 'FLAG' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-green-100 text-green-700'
                }`}>
                  {log.decision}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// 🏛️ Main Government Dashboard Component
const GovernmentDashboard = () => {
  const [activeTab, setActiveTab] = useState('citizen');
  const [currentUser] = useState('dashboard_user'); // Set from your auth system

  const tabs = [
    { id: 'citizen', label: '👥 Citizen Lookup', component: CitizenLookup },
    { id: 'dmv', label: '🚗 DMV Records', component: DMVLookup },
    { id: 'metrics', label: '📊 Metrics', component: ProtectionMetrics }
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-3xl font-bold text-gray-900">
              🏛️ Government Dashboard
            </h1>
            <div className="text-sm text-gray-600">
              🛡️ Protected by Jimini AI • User: {currentUser}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <nav className="flex space-x-4">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-md font-medium ${
                  activeTab === tab.id
                    ? 'bg-blue-500 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div>
          {tabs.map((tab) => {
            if (tab.id === activeTab) {
              const Component = tab.component;
              return <Component key={tab.id} userId={currentUser} />;
            }
            return null;
          })}
        </div>
      </div>
    </div>
  );
};

export {
  GovernmentDashboard,
  CitizenLookup,
  DMVLookup,
  ProtectionMetrics,
  ProtectedInput,
  usePIIProtection
};