// React Rule Management Components
// ==================================

import React, { useState, useEffect } from 'react';
import axios from 'axios';

// API Base URL
const API_BASE = 'http://localhost:5000/api';

// 🔧 Rules Management Component
const RulesManager = () => {
  const [rules, setRules] = useState({});
  const [loading, setLoading] = useState(true);
  const [editingRule, setEditingRule] = useState(null);
  const [newRule, setNewRule] = useState({
    id: '',
    name: '',
    pattern: '',
    action: 'FLAG',
    severity: 'MEDIUM',
    enabled: true
  });

  // Load rules from API
  const loadRules = async () => {
    try {
      const response = await axios.get(`${API_BASE}/rules`);
      setRules(response.data.rules);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load rules:', error);
      setLoading(false);
    }
  };

  // Toggle rule enabled/disabled
  const toggleRule = async (ruleId) => {
    try {
      const response = await axios.post(`${API_BASE}/rules/${ruleId}/toggle`);
      if (response.data.status === 'success') {
        await loadRules(); // Reload rules
      }
    } catch (error) {
      console.error('Failed to toggle rule:', error);
    }
  };

  // Update existing rule
  const updateRule = async (ruleId, updates) => {
    try {
      const response = await axios.put(`${API_BASE}/rules/${ruleId}`, updates);
      if (response.data.status === 'success') {
        await loadRules();
        setEditingRule(null);
      }
    } catch (error) {
      console.error('Failed to update rule:', error);
      alert('Failed to update rule: ' + (error.response?.data?.error || error.message));
    }
  };

  // Add new rule
  const addRule = async () => {
    try {
      const response = await axios.post(`${API_BASE}/rules`, newRule);
      if (response.data.status === 'success') {
        await loadRules();
        setNewRule({
          id: '',
          name: '',
          pattern: '',
          action: 'FLAG',
          severity: 'MEDIUM',
          enabled: true
        });
      }
    } catch (error) {
      console.error('Failed to add rule:', error);
      alert('Failed to add rule: ' + (error.response?.data?.error || error.message));
    }
  };

  // Reload rules from file
  const reloadRules = async () => {
    try {
      const response = await axios.post(`${API_BASE}/rules/reload`);
      if (response.data.status === 'success') {
        await loadRules();
        alert('Rules reloaded successfully!');
      }
    } catch (error) {
      console.error('Failed to reload rules:', error);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  if (loading) {
    return <div className="p-6">Loading rules...</div>;
  }

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getActionColor = (action) => {
    switch (action?.toLowerCase()) {
      case 'block': return 'text-red-600 bg-red-100';
      case 'flag': return 'text-yellow-600 bg-yellow-100';
      case 'allow': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">🔧 PII Protection Rules Management</h2>
        <button
          onClick={reloadRules}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          🔄 Reload from File
        </button>
      </div>

      {/* Rules List */}
      <div className="space-y-4 mb-8">
        {Object.entries(rules).map(([ruleId, rule]) => (
          <div key={ruleId} className={`border rounded-lg p-4 ${rule.enabled ? 'border-green-300 bg-green-50' : 'border-gray-300 bg-gray-50'}`}>
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold">{rule.name}</h3>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getActionColor(rule.action)}`}>
                    {rule.action}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(rule.severity)}`}>
                    {rule.severity}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${rule.enabled ? 'text-green-700 bg-green-100' : 'text-gray-700 bg-gray-100'}`}>
                    {rule.enabled ? 'ENABLED' : 'DISABLED'}
                  </span>
                </div>
                
                <div className="text-sm text-gray-600 mb-2">
                  <strong>Rule ID:</strong> {ruleId}
                </div>
                
                <div className="text-sm text-gray-600 mb-2">
                  <strong>Pattern:</strong> 
                  <code className="ml-2 px-2 py-1 bg-gray-100 rounded text-xs">
                    {rule.pattern}
                  </code>
                </div>
                
                {editingRule === ruleId && (
                  <div className="mt-4 p-4 border border-blue-300 rounded bg-blue-50">
                    <h4 className="font-semibold mb-3">Edit Rule</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <input
                        type="text"
                        placeholder="Rule Name"
                        defaultValue={rule.name}
                        onChange={(e) => rule.editName = e.target.value}
                        className="p-2 border rounded"
                      />
                      <select
                        defaultValue={rule.action}
                        onChange={(e) => rule.editAction = e.target.value}
                        className="p-2 border rounded"
                      >
                        <option value="BLOCK">BLOCK</option>
                        <option value="FLAG">FLAG</option>
                        <option value="ALLOW">ALLOW</option>
                      </select>
                      <input
                        type="text"
                        placeholder="Regex Pattern"
                        defaultValue={rule.pattern}
                        onChange={(e) => rule.editPattern = e.target.value}
                        className="p-2 border rounded md:col-span-2"
                      />
                      <select
                        defaultValue={rule.severity}
                        onChange={(e) => rule.editSeverity = e.target.value}
                        className="p-2 border rounded"
                      >
                        <option value="CRITICAL">CRITICAL</option>
                        <option value="HIGH">HIGH</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="LOW">LOW</option>
                      </select>
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          defaultChecked={rule.enabled}
                          onChange={(e) => rule.editEnabled = e.target.checked}
                        />
                        <span>Enabled</span>
                      </label>
                    </div>
                    <div className="mt-4 space-x-2">
                      <button
                        onClick={() => {
                          const updates = {};
                          if (rule.editName !== undefined) updates.name = rule.editName;
                          if (rule.editPattern !== undefined) updates.pattern = rule.editPattern;
                          if (rule.editAction !== undefined) updates.action = rule.editAction;
                          if (rule.editSeverity !== undefined) updates.severity = rule.editSeverity;
                          if (rule.editEnabled !== undefined) updates.enabled = rule.editEnabled;
                          updateRule(ruleId, updates);
                        }}
                        className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                      >
                        💾 Save Changes
                      </button>
                      <button
                        onClick={() => setEditingRule(null)}
                        className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                      >
                        ❌ Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="flex space-x-2 ml-4">
                <button
                  onClick={() => setEditingRule(editingRule === ruleId ? null : ruleId)}
                  className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                >
                  ✏️ Edit
                </button>
                <button
                  onClick={() => toggleRule(ruleId)}
                  className={`px-3 py-1 text-white rounded text-sm ${
                    rule.enabled 
                      ? 'bg-red-500 hover:bg-red-600' 
                      : 'bg-green-500 hover:bg-green-600'
                  }`}
                >
                  {rule.enabled ? '🚫 Disable' : '✅ Enable'}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add New Rule */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold mb-4">➕ Add New Rule</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Rule ID (e.g., CUSTOM-PROTECTION)"
            value={newRule.id}
            onChange={(e) => setNewRule({...newRule, id: e.target.value})}
            className="p-2 border rounded"
          />
          <input
            type="text"
            placeholder="Rule Name"
            value={newRule.name}
            onChange={(e) => setNewRule({...newRule, name: e.target.value})}
            className="p-2 border rounded"
          />
          <input
            type="text"
            placeholder="Regex Pattern"
            value={newRule.pattern}
            onChange={(e) => setNewRule({...newRule, pattern: e.target.value})}
            className="p-2 border rounded md:col-span-2"
          />
          <select
            value={newRule.action}
            onChange={(e) => setNewRule({...newRule, action: e.target.value})}
            className="p-2 border rounded"
          >
            <option value="BLOCK">BLOCK</option>
            <option value="FLAG">FLAG</option>
            <option value="ALLOW">ALLOW</option>
          </select>
          <select
            value={newRule.severity}
            onChange={(e) => setNewRule({...newRule, severity: e.target.value})}
            className="p-2 border rounded"
          >
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>
        <button
          onClick={addRule}
          disabled={!newRule.id || !newRule.name || !newRule.pattern}
          className="mt-4 px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ➕ Add Rule
        </button>
      </div>
    </div>
  );
};

// 📊 Enhanced Protection Metrics with Rule Status
const EnhancedProtectionMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsResponse, healthResponse] = await Promise.all([
          axios.get(`${API_BASE}/metrics`),
          axios.get(`${API_BASE}/health`)
        ]);
        
        setMetrics(metricsResponse.data.metrics);
        setHealth(healthResponse.data);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!metrics || !health) {
    return <div className="p-6">Loading metrics...</div>;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6">📊 Enhanced Protection Metrics</h2>
      
      {/* System Health */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">🔧 System Health</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-xl font-bold text-blue-600">{health.rules_active}</div>
            <div className="text-sm text-blue-600">Active Rules</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-green-600">{health.rules_total}</div>
            <div className="text-sm text-green-600">Total Rules</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-purple-600">{health.audit_entries}</div>
            <div className="text-sm text-purple-600">Audit Entries</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-green-600">{health.status}</div>
            <div className="text-sm text-green-600">Service Status</div>
          </div>
        </div>
      </div>

      {/* Protection Stats */}
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

      {/* Rules Summary */}
      {health.rules_summary && (
        <div>
          <h3 className="text-lg font-semibold mb-3">🔍 Rules Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {Object.entries(health.rules_summary).map(([ruleId, status]) => (
              <div key={ruleId} className={`p-2 rounded text-sm ${
                status.enabled 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-gray-700'
              }`}>
                <div className="font-medium">{ruleId}</div>
                <div className="text-xs">
                  {status.enabled ? '✅ Enabled' : '❌ Disabled'} • {status.action}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export { RulesManager, EnhancedProtectionMetrics };