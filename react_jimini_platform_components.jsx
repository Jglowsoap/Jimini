import React, { useState, useEffect } from 'react';
import axios from 'axios';

// 🏛️ **FULL JIMINI PLATFORM REACT COMPONENTS**

// Hook for Jimini Platform integration
export const useJiminiPlatform = (baseURL = 'http://localhost:5001') => {
  const [jiminiHealth, setJiminiHealth] = useState(null);
  const [connected, setConnected] = useState(false);

  const checkJiminiHealth = async () => {
    try {
      const response = await axios.get(`${baseURL}/api/jimini/health`);
      setJiminiHealth(response.data);
      setConnected(response.data.jimini_connected);
      return response.data;
    } catch (error) {
      console.error('Jimini health check failed:', error);
      setConnected(false);
      return null;
    }
  };

  const evaluateWithJimini = async (text, endpoint = '/dashboard/default', userId = 'react_user') => {
    try {
      const response = await axios.post(`${baseURL}/api/jimini/evaluate`, {
        text,
        endpoint,
        user_id: userId,
        agent_id: 'react_dashboard'
      });
      return response.data;
    } catch (error) {
      console.error('Jimini evaluation failed:', error);
      return {
        status: 'error',
        decision: 'ALLOW',
        message: 'Jimini evaluation failed - defaulting to allow',
        fallback_mode: true
      };
    }
  };

  const getJiminiMetrics = async () => {
    try {
      const response = await axios.get(`${baseURL}/api/jimini/metrics`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch Jimini metrics:', error);
      return { status: 'error', message: 'Could not fetch metrics' };
    }
  };

  const getAuditVerification = async () => {
    try {
      const response = await axios.get(`${baseURL}/api/jimini/audit/verify`);
      return response.data;
    } catch (error) {
      console.error('Failed to verify audit chain:', error);
      return { status: 'error', message: 'Could not verify audit chain' };
    }
  };

  const getSarifReport = async () => {
    try {
      const response = await axios.get(`${baseURL}/api/jimini/audit/sarif`);
      return response.data;
    } catch (error) {
      console.error('Failed to get SARIF report:', error);
      return { status: 'error', message: 'Could not generate SARIF report' };
    }
  };

  const reloadRules = async () => {
    try {
      const response = await axios.post(`${baseURL}/api/jimini/rules/reload`);
      return response.data;
    } catch (error) {
      console.error('Failed to reload rules:', error);
      return { status: 'error', message: 'Could not reload rules' };
    }
  };

  useEffect(() => {
    checkJiminiHealth();
    const interval = setInterval(checkJiminiHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return {
    jiminiHealth,
    connected,
    checkJiminiHealth,
    evaluateWithJimini,
    getJiminiMetrics,
    getAuditVerification,
    getSarifReport,
    reloadRules
  };
};

// Jimini Platform Status Component
export const JiminiPlatformStatus = ({ baseURL }) => {
  const { jiminiHealth, connected, checkJiminiHealth } = useJiminiPlatform(baseURL);

  const getStatusColor = () => {
    if (connected) return 'text-green-600 bg-green-100';
    return 'text-red-600 bg-red-100';
  };

  const getStatusIcon = () => {
    if (connected) return '✅';
    return '❌';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-800">🛡️ Jimini Platform Status</h2>
        <button 
          onClick={checkJiminiHealth}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Refresh
        </button>
      </div>
      
      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor()}`}>
        <span className="mr-2">{getStatusIcon()}</span>
        {connected ? 'Jimini Platform Connected' : 'Jimini Platform Disconnected'}
      </div>
      
      {jiminiHealth && (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">Service</div>
            <div className="font-semibold">{jiminiHealth.service}</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">Version</div>
            <div className="font-semibold">{jiminiHealth.version}</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">Jimini URL</div>
            <div className="font-semibold text-xs">{jiminiHealth.jimini_url}</div>
          </div>
        </div>
      )}
      
      {jiminiHealth && jiminiHealth.features && (
        <div className="mt-4">
          <div className="text-sm text-gray-600 mb-2">Enterprise Features:</div>
          <div className="flex flex-wrap gap-2">
            {jiminiHealth.features.map((feature, index) => (
              <span 
                key={index}
                className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
              >
                {feature.replace('_', ' ')}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Enhanced Protected Input with Full Jimini
export const JiminiProtectedInput = ({ 
  placeholder = "Enter text...", 
  value, 
  onChange, 
  endpoint = '/dashboard/input',
  userId = 'dashboard_user',
  baseURL = 'http://localhost:5001',
  onJiminiResult = () => {},
  className = ""
}) => {
  const [jiminiResult, setJiminiResult] = useState(null);
  const [isChecking, setIsChecking] = useState(false);
  const { evaluateWithJimini, connected } = useJiminiPlatform(baseURL);

  const checkWithJimini = async (text) => {
    if (!text.trim() || !connected) return;
    
    setIsChecking(true);
    try {
      const result = await evaluateWithJimini(text, endpoint, userId);
      setJiminiResult(result);
      onJiminiResult(result);
    } catch (error) {
      console.error('Jimini check failed:', error);
    } finally {
      setIsChecking(false);
    }
  };

  const handleChange = (e) => {
    const newValue = e.target.value;
    onChange(e);
    
    // Debounced Jimini check
    clearTimeout(window.jiminiTimeout);
    window.jiminiTimeout = setTimeout(() => {
      checkWithJimini(newValue);
    }, 1000);
  };

  const getInputStyle = () => {
    if (!jiminiResult) return "border-gray-300";
    
    switch (jiminiResult.decision) {
      case 'BLOCK':
        return "border-red-500 bg-red-50";
      case 'FLAG':
        return "border-yellow-500 bg-yellow-50";
      default:
        return "border-green-500 bg-green-50";
    }
  };

  const getStatusIcon = () => {
    if (isChecking) return "⏳";
    if (!jiminiResult) return "🛡️";
    
    switch (jiminiResult.decision) {
      case 'BLOCK':
        return "🚫";
      case 'FLAG':
        return "⚠️";
      default:
        return "✅";
    }
  };

  return (
    <div className={`relative ${className}`}>
      <div className="flex items-center">
        <input
          type="text"
          placeholder={placeholder}
          value={value}
          onChange={handleChange}
          disabled={jiminiResult?.decision === 'BLOCK'}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${getInputStyle()}`}
        />
        <span className="ml-2 text-lg" title={connected ? "Jimini Platform Active" : "Jimini Platform Disconnected"}>
          {getStatusIcon()}
        </span>
      </div>
      
      {jiminiResult && (
        <div className="mt-2 text-sm">
          <div className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
            jiminiResult.decision === 'BLOCK' ? 'bg-red-100 text-red-800' :
            jiminiResult.decision === 'FLAG' ? 'bg-yellow-100 text-yellow-800' :
            'bg-green-100 text-green-800'
          }`}>
            Jimini: {jiminiResult.decision}
            {jiminiResult.rule_ids && jiminiResult.rule_ids.length > 0 && (
              <span className="ml-1">({jiminiResult.rule_ids.join(', ')})</span>
            )}
          </div>
          
          {jiminiResult.message && (
            <div className="mt-1 text-gray-600 text-xs">
              {jiminiResult.message}
            </div>
          )}
          
          {jiminiResult.audit_logged && (
            <div className="mt-1 text-xs text-blue-600">
              🔒 Audit logged with tamper-proof chain
            </div>
          )}
          
          {jiminiResult.jimini_version === 'enterprise' && (
            <div className="mt-1 text-xs text-purple-600">
              ⭐ Enterprise Jimini Platform
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Jimini Analytics Dashboard
export const JiminiAnalyticsDashboard = ({ baseURL = 'http://localhost:5001' }) => {
  const [metrics, setMetrics] = useState(null);
  const [auditVerification, setAuditVerification] = useState(null);
  const [loading, setLoading] = useState(false);
  const { getJiminiMetrics, getAuditVerification, connected } = useJiminiPlatform(baseURL);

  const loadAnalytics = async () => {
    if (!connected) return;
    
    setLoading(true);
    try {
      const [metricsResult, auditResult] = await Promise.all([
        getJiminiMetrics(),
        getAuditVerification()
      ]);
      
      setMetrics(metricsResult);
      setAuditVerification(auditResult);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
    const interval = setInterval(loadAnalytics, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [connected]);

  if (!connected) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">📊 Jimini Analytics</h3>
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-2">🔌</div>
          <div>Connect to Jimini Platform to view analytics</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">📊 Jimini Enterprise Analytics</h3>
        <button 
          onClick={loadAnalytics}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>
      
      {metrics && metrics.status === 'success' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-blue-800 text-sm font-medium">Total Evaluations</div>
            <div className="text-2xl font-bold text-blue-900">
              {metrics.metrics?.evaluations_total || 0}
            </div>
          </div>
          
          <div className="bg-red-50 p-4 rounded-lg">
            <div className="text-red-800 text-sm font-medium">Blocked Requests</div>
            <div className="text-2xl font-bold text-red-900">
              {metrics.metrics?.blocked_total || 0}
            </div>
          </div>
          
          <div className="bg-yellow-50 p-4 rounded-lg">
            <div className="text-yellow-800 text-sm font-medium">Flagged Requests</div>
            <div className="text-2xl font-bold text-yellow-900">
              {metrics.metrics?.flagged_total || 0}
            </div>
          </div>
          
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-green-800 text-sm font-medium">Allowed Requests</div>
            <div className="text-2xl font-bold text-green-900">
              {metrics.metrics?.allowed_total || 0}
            </div>
          </div>
        </div>
      )}
      
      {auditVerification && auditVerification.status === 'success' && (
        <div className="bg-purple-50 p-4 rounded-lg">
          <h4 className="font-semibold text-purple-800 mb-2">🔒 Audit Chain Verification</h4>
          <div className="text-sm text-purple-700">
            <div>Chain Status: <span className="font-medium">
              {auditVerification.audit_verification?.chain_valid ? '✅ Valid' : '❌ Invalid'}
            </span></div>
            <div>Total Records: <span className="font-medium">
              {auditVerification.audit_verification?.total_records || 0}
            </span></div>
            <div>Tamper Proof: <span className="font-medium">
              {auditVerification.tamper_proof ? '🛡️ Yes' : '⚠️ No'}
            </span></div>
          </div>
        </div>
      )}
    </div>
  );
};

// Enhanced Government Citizen Lookup with Jimini
export const JiminiGovernmentCitizenLookup = ({ 
  userId = 'government_user', 
  baseURL = 'http://localhost:5001' 
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [justification, setJustification] = useState('');
  const [loading, setLoading] = useState(false);
  const { connected } = useJiminiPlatform(baseURL);

  const handleLookup = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${baseURL}/api/government/citizen/lookup`, {
        query,
        justification,
        user_id: userId
      });
      
      setResults(response.data);
    } catch (error) {
      console.error('Citizen lookup failed:', error);
      if (error.response?.status === 403) {
        setResults({
          status: 'blocked',
          message: error.response.data.message,
          jimini_blocked: true
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const getResultStyle = () => {
    if (!results) return '';
    
    switch (results.status) {
      case 'blocked':
        return 'border-red-500 bg-red-50';
      case 'success':
        return 'border-green-500 bg-green-50';
      default:
        return 'border-gray-300';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        🏛️ Government Citizen Lookup {connected ? '(Jimini Protected)' : '(Jimini Disconnected)'}
      </h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search Query
          </label>
          <JiminiProtectedInput
            placeholder="Enter citizen search criteria..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            endpoint="/government/citizen/lookup"
            userId={userId}
            baseURL={baseURL}
            className="w-full"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Justification (Required for audit trail)
          </label>
          <textarea
            placeholder="Enter legal justification for this lookup..."
            value={justification}
            onChange={(e) => setJustification(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
          />
        </div>
        
        <button
          onClick={handleLookup}
          disabled={loading || !connected}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Searching...' : 'Lookup Citizen'}
        </button>
      </div>
      
      {results && (
        <div className={`mt-4 p-4 border rounded-lg ${getResultStyle()}`}>
          <h4 className="font-semibold mb-2">Lookup Results:</h4>
          
          {results.status === 'blocked' && (
            <div className="text-red-800">
              <div className="font-medium">🚫 Access Blocked by Jimini AI</div>
              <div className="text-sm mt-1">{results.message}</div>
              {results.jimini_result && (
                <div className="text-xs mt-2 bg-red-100 p-2 rounded">
                  Rules triggered: {results.jimini_result.rule_ids?.join(', ')}
                </div>
              )}
            </div>
          )}
          
          {results.status === 'success' && results.citizen_data && (
            <div className="text-green-800">
              <div className="font-medium">✅ Citizen Found</div>
              <div className="mt-2 space-y-1 text-sm">
                <div>ID: {results.citizen_data.citizen_id}</div>
                <div>Name: {results.citizen_data.name}</div>
                <div>Status: {results.citizen_data.status}</div>
                <div>Last Verified: {results.citizen_data.last_verified}</div>
              </div>
              
              {results.query_protection && (
                <div className="mt-3 text-xs bg-blue-100 p-2 rounded">
                  <div>🛡️ Jimini Protection Applied</div>
                  <div>Query Decision: {results.query_protection.decision}</div>
                  <div>Response Decision: {results.response_protection?.decision}</div>
                  {results.query_protection.audit_logged && (
                    <div>🔒 Audit logged with enterprise security</div>
                  )}
                </div>
              )}
            </div>
          )}
          
          {results.status === 'not_found' && (
            <div className="text-gray-600">
              <div className="font-medium">ℹ️ No Results Found</div>
              <div className="text-sm mt-1">No citizen found matching your search criteria.</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Compliance & SARIF Report Generator
export const JiminiComplianceReports = ({ baseURL = 'http://localhost:5001' }) => {
  const [sarifReport, setSarifReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const { getSarifReport, connected } = useJiminiPlatform(baseURL);

  const generateSarifReport = async () => {
    if (!connected) return;
    
    setLoading(true);
    try {
      const report = await getSarifReport();
      setSarifReport(report);
    } catch (error) {
      console.error('Failed to generate SARIF report:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadSarifReport = () => {
    if (!sarifReport?.sarif_report) return;
    
    const blob = new Blob([JSON.stringify(sarifReport.sarif_report, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `jimini-compliance-report-${new Date().toISOString().split('T')[0]}.sarif`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        📋 Government Compliance Reports
      </h3>
      
      {!connected ? (
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-2">🔌</div>
          <div>Connect to Jimini Platform to generate compliance reports</div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-800 mb-2">SARIF Compliance Report</h4>
            <p className="text-blue-700 text-sm mb-3">
              Generate a standardized SARIF (Static Analysis Results Interchange Format) 
              report for government compliance requirements.
            </p>
            
            <button
              onClick={generateSarifReport}
              disabled={loading}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Generating...' : 'Generate SARIF Report'}
            </button>
          </div>
          
          {sarifReport && sarifReport.status === 'success' && (
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-green-800">✅ Report Generated</h4>
                <button
                  onClick={downloadSarifReport}
                  className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
                >
                  Download SARIF
                </button>
              </div>
              
              <div className="text-green-700 text-sm space-y-1">
                <div>Format: {sarifReport.compliance_format}</div>
                <div>Government Ready: {sarifReport.government_ready ? '✅ Yes' : '❌ No'}</div>
                <div>Generated: {new Date().toLocaleString()}</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Main Jimini Platform Dashboard
export const JiminiPlatformDashboard = ({ baseURL = 'http://localhost:5001' }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const { reloadRules, connected } = useJiminiPlatform(baseURL);

  const handleReloadRules = async () => {
    const result = await reloadRules();
    if (result.status === 'success') {
      alert('✅ Jimini rules reloaded successfully!');
    } else {
      alert('❌ Failed to reload rules: ' + result.message);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: '📊' },
    { id: 'citizen-lookup', name: 'Citizen Lookup', icon: '🏛️' },
    { id: 'analytics', name: 'Analytics', icon: '📈' },
    { id: 'compliance', name: 'Compliance', icon: '📋' },
    { id: 'rules', name: 'Rules Management', icon: '⚙️' }
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                🛡️ Government Dashboard - Jimini Platform
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              {connected && (
                <button
                  onClick={handleReloadRules}
                  className="px-3 py-1 bg-purple-500 text-white text-sm rounded hover:bg-purple-600 transition-colors"
                >
                  🔄 Reload Rules
                </button>
              )}
              
              <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                connected 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {connected ? '✅ Jimini Connected' : '❌ Jimini Disconnected'}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <nav className="flex space-x-8">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
        
        <div className="space-y-6">
          {activeTab === 'overview' && (
            <>
              <JiminiPlatformStatus baseURL={baseURL} />
              <JiminiAnalyticsDashboard baseURL={baseURL} />
            </>
          )}
          
          {activeTab === 'citizen-lookup' && (
            <JiminiGovernmentCitizenLookup baseURL={baseURL} />
          )}
          
          {activeTab === 'analytics' && (
            <JiminiAnalyticsDashboard baseURL={baseURL} />
          )}
          
          {activeTab === 'compliance' && (
            <JiminiComplianceReports baseURL={baseURL} />
          )}
          
          {activeTab === 'rules' && connected && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">⚙️ Rules Management</h3>
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-blue-800 mb-3">
                  Rules are managed through YAML files and hot-reloaded automatically.
                  Edit your rules in <code>policy_rules.yaml</code> or rule packs in <code>packs/</code>.
                </p>
                <button
                  onClick={handleReloadRules}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                >
                  🔄 Force Reload Rules Now
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default JiminiPlatformDashboard;