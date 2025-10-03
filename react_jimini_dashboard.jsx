import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// 🛡️ **JIMINI GATEWAY CLIENT**

class JiminiGatewayClient {
  constructor(baseUrl = 'http://localhost:8000', tenantId = 'gov-agency-a') {
    this.baseUrl = baseUrl;
    this.tenantId = tenantId;
    this.sessionId = `session_${Date.now()}`;
    
    // Configure axios with default headers
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'X-Tenant-Id': tenantId,
        'X-Session-Id': this.sessionId,
        'Content-Type': 'application/json'
      }
    });
  }
  
  async getDecisions(filters = {}) {
    try {
      const response = await this.client.get('/api/v1/decisions', { params: filters });
      return response.data;
    } catch (error) {
      console.error('Error fetching decisions:', error);
      throw error;
    }
  }
  
  async getDecision(requestId) {
    try {
      const response = await this.client.get(`/api/v1/decisions/${requestId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching decision:', error);
      throw error;
    }
  }
  
  async getRules() {
    try {
      const response = await this.client.get('/api/v1/rules');
      return response.data;
    } catch (error) {
      console.error('Error fetching rules:', error);
      throw error;
    }
  }
  
  async validateRule(rule) {
    try {
      const response = await this.client.post('/api/v1/rules/validate', rule);
      return response.data;
    } catch (error) {
      console.error('Error validating rule:', error);
      throw error;
    }
  }
  
  async dryrunRule(rule, testContent) {
    try {
      const response = await this.client.post('/api/v1/rules/dryrun', {
        ...rule,
        test_content: testContent
      });
      return response.data;
    } catch (error) {
      console.error('Error running rule dry-run:', error);
      throw error;
    }
  }
  
  async publishRule(rule) {
    try {
      const response = await this.client.post('/api/v1/rules/publish', rule);
      return response.data;
    } catch (error) {
      console.error('Error publishing rule:', error);
      throw error;
    }
  }
  
  async getCoverage() {
    try {
      const response = await this.client.get('/api/v1/coverage');
      return response.data;
    } catch (error) {
      console.error('Error fetching coverage:', error);
      throw error;
    }
  }
  
  async getProposals() {
    try {
      const response = await this.client.get('/api/v1/policies/proposals');
      return response.data;
    } catch (error) {
      console.error('Error fetching proposals:', error);
      throw error;
    }
  }
  
  async approveProposal(proposalId, reviewer) {
    try {
      const response = await this.client.post(`/api/v1/policies/proposals/${proposalId}/approve`, {
        reviewer
      });
      return response.data;
    } catch (error) {
      console.error('Error approving proposal:', error);
      throw error;
    }
  }
  
  async revealField(requestId, field, reason) {
    try {
      const response = await this.client.post('/api/v1/reveal', {
        request_id: requestId,
        field,
        reason
      });
      return response.data;
    } catch (error) {
      console.error('Error revealing field:', error);
      throw error;
    }
  }
}

// 📊 **DASHBOARD COMPONENTS**

// Coverage Metrics Component
const CoverageMetrics = ({ client }) => {
  const [coverage, setCoverage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const fetchCoverage = useCallback(async () => {
    try {
      setLoading(true);
      const response = await client.getCoverage();
      if (response.code === 'ok') {
        setCoverage(response.data);
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [client]);
  
  useEffect(() => {
    fetchCoverage();
    const interval = setInterval(fetchCoverage, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [fetchCoverage]);
  
  if (loading) return <div className="loading">Loading coverage metrics...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!coverage) return <div className="no-data">No coverage data available</div>;
  
  return (
    <div className="coverage-metrics">
      <h3>🛡️ Policy Enforcement Coverage</h3>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-value">{coverage.total_requests}</div>
          <div className="metric-label">Total Requests</div>
        </div>
        
        <div className="metric-card blocked">
          <div className="metric-value">{coverage.blocked}</div>
          <div className="metric-label">Blocked</div>
        </div>
        
        <div className="metric-card flagged">
          <div className="metric-value">{coverage.flagged}</div>
          <div className="metric-label">Flagged</div>
        </div>
        
        <div className="metric-card allowed">
          <div className="metric-value">{coverage.allowed}</div>
          <div className="metric-label">Allowed</div>
        </div>
        
        <div className="metric-card coverage-rate">
          <div className="metric-value">{coverage.coverage_rate.toFixed(1)}%</div>
          <div className="metric-label">Coverage Rate</div>
        </div>
        
        <div className="metric-card rules">
          <div className="metric-value">{coverage.active_rules}</div>
          <div className="metric-label">Active Rules</div>
        </div>
      </div>
      
      <div className="systems-breakdown">
        <h4>📡 System Breakdown</h4>
        <div className="systems-grid">
          {Object.entries(coverage.systems || {}).map(([system, stats]) => (
            <div key={system} className="system-card">
              <div className="system-name">{system.replace('_', ' ').toUpperCase()}</div>
              <div className="system-stats">
                <span className="stat blocked">🚫 {stats.blocked}</span>
                <span className="stat flagged">⚠️ {stats.flagged}</span>
                <span className="stat allowed">✅ {stats.allowed}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Decisions Log Component
const DecisionsLog = ({ client }) => {
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({ 
    system: '', 
    decision: '', 
    limit: 50,
    offset: 0 
  });
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [revealModal, setRevealModal] = useState(null);
  
  const fetchDecisions = useCallback(async () => {
    try {
      setLoading(true);
      const cleanFilters = Object.fromEntries(
        Object.entries(filters).filter(([_, value]) => value !== '')
      );
      const response = await client.getDecisions(cleanFilters);
      if (response.code === 'ok') {
        setDecisions(response.data.decisions);
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [client, filters]);
  
  useEffect(() => {
    fetchDecisions();
  }, [fetchDecisions]);
  
  const handleRevealField = async (field, reason) => {
    try {
      if (!selectedDecision || !field || !reason) return;
      
      const response = await client.revealField(selectedDecision.request_id, field, reason);
      if (response.code === 'ok') {
        alert(`Field revealed: ${field}\nReason logged: ${reason}`);
        setRevealModal(null);
      } else {
        alert(`Error: ${response.message}`);
      }
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };
  
  const getDecisionIcon = (decision) => {
    switch (decision) {
      case 'block': return '🚫';
      case 'flag': return '⚠️';
      case 'allow': return '✅';
      default: return '❓';
    }
  };
  
  const getSystemIcon = (system) => {
    switch (system) {
      case 'ldap': return '🗂️';
      case 'entrust_idg': return '🔐';
      case 'ums': return '👤';
      case 'db2': return '🗄️';
      case 'service_now': return '🎟️';
      case 'llm': return '🤖';
      default: return '📡';
    }
  };
  
  return (
    <div className="decisions-log">
      <div className="decisions-header">
        <h3>📋 Policy Decisions Log</h3>
        
        <div className="filters">
          <select 
            value={filters.system} 
            onChange={(e) => setFilters(prev => ({ ...prev, system: e.target.value }))}
          >
            <option value="">All Systems</option>
            <option value="ldap">LDAP</option>
            <option value="entrust_idg">Entrust IDG</option>
            <option value="ums">UMS</option>
            <option value="db2">DB2</option>
            <option value="service_now">ServiceNow</option>
            <option value="llm">LLM</option>
          </select>
          
          <select 
            value={filters.decision} 
            onChange={(e) => setFilters(prev => ({ ...prev, decision: e.target.value }))}
          >
            <option value="">All Decisions</option>
            <option value="block">Blocked</option>
            <option value="flag">Flagged</option>
            <option value="allow">Allowed</option>
          </select>
          
          <button onClick={fetchDecisions} className="refresh-btn">🔄 Refresh</button>
        </div>
      </div>
      
      {loading && <div className="loading">Loading decisions...</div>}
      {error && <div className="error">Error: {error}</div>}
      
      {!loading && !error && (
        <div className="decisions-table">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>System</th>
                <th>Endpoint</th>
                <th>Decision</th>
                <th>Rules</th>
                <th>Masked Fields</th>
                <th>Latency</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {decisions.map((decision) => (
                <tr key={decision.request_id} className={`decision-row ${decision.decision}`}>
                  <td>{new Date(decision.ts).toLocaleString()}</td>
                  <td>
                    {getSystemIcon(decision.system)} {decision.system.replace('_', ' ').toUpperCase()}
                  </td>
                  <td>{decision.endpoint}</td>
                  <td>
                    {getDecisionIcon(decision.decision)} {decision.decision.toUpperCase()}
                  </td>
                  <td>
                    <div className="rule-badges">
                      {decision.rule_ids.map(ruleId => (
                        <span key={ruleId} className="rule-badge">{ruleId}</span>
                      ))}
                    </div>
                  </td>
                  <td>
                    {decision.masked_fields.length > 0 ? (
                      <div className="masked-fields">
                        {decision.masked_fields.map(field => (
                          <span key={field} className="masked-field">{field}</span>
                        ))}
                      </div>
                    ) : (
                      <span className="no-masking">None</span>
                    )}
                  </td>
                  <td>{decision.latency_ms.toFixed(1)}ms</td>
                  <td>
                    <button 
                      onClick={() => setSelectedDecision(decision)}
                      className="view-btn"
                    >
                      👁️ View
                    </button>
                    {decision.masked_fields.length > 0 && (
                      <button 
                        onClick={() => {
                          setSelectedDecision(decision);
                          setRevealModal({
                            field: decision.masked_fields[0],
                            reason: ''
                          });
                        }}
                        className="reveal-btn"
                      >
                        🔓 Reveal
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Decision Detail Modal */}
      {selectedDecision && !revealModal && (
        <div className="modal-overlay" onClick={() => setSelectedDecision(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h4>📋 Decision Details</h4>
              <button onClick={() => setSelectedDecision(null)} className="close-btn">✕</button>
            </div>
            
            <div className="decision-details">
              <div className="detail-section">
                <h5>Request Information</h5>
                <p><strong>Request ID:</strong> {selectedDecision.request_id}</p>
                <p><strong>Timestamp:</strong> {new Date(selectedDecision.ts).toLocaleString()}</p>
                <p><strong>System:</strong> {selectedDecision.system}</p>
                <p><strong>Endpoint:</strong> {selectedDecision.endpoint}</p>
                <p><strong>Direction:</strong> {selectedDecision.direction}</p>
              </div>
              
              <div className="detail-section">
                <h5>Policy Decision</h5>
                <p><strong>Decision:</strong> 
                  <span className={`decision-badge ${selectedDecision.decision}`}>
                    {getDecisionIcon(selectedDecision.decision)} {selectedDecision.decision.toUpperCase()}
                  </span>
                </p>
                <p><strong>Latency:</strong> {selectedDecision.latency_ms.toFixed(1)}ms</p>
              </div>
              
              {selectedDecision.rule_ids.length > 0 && (
                <div className="detail-section">
                  <h5>Triggered Rules</h5>
                  <div className="rules-list">
                    {selectedDecision.rule_ids.map(ruleId => (
                      <span key={ruleId} className="rule-tag">{ruleId}</span>
                    ))}
                  </div>
                </div>
              )}
              
              {selectedDecision.citations.length > 0 && (
                <div className="detail-section">
                  <h5>Policy Citations</h5>
                  <div className="citations-list">
                    {selectedDecision.citations.map((citation, idx) => (
                      <div key={idx} className="citation">
                        <strong>{citation.doc}</strong> - Section {citation.section}
                        <br />
                        <a href={citation.url} target="_blank" rel="noopener noreferrer">
                          {citation.url}
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {selectedDecision.masked_fields.length > 0 && (
                <div className="detail-section">
                  <h5>Masked Fields</h5>
                  <div className="masked-fields-list">
                    {selectedDecision.masked_fields.map(field => (
                      <div key={field} className="masked-field-item">
                        <span className="field-name">{field}</span>
                        <button 
                          onClick={() => setRevealModal({ field, reason: '' })}
                          className="field-reveal-btn"
                        >
                          🔓 Break Glass
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Reveal Field Modal */}
      {revealModal && (
        <div className="modal-overlay" onClick={() => setRevealModal(null)}>
          <div className="modal-content reveal-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h4>🔓 Break Glass Access</h4>
              <button onClick={() => setRevealModal(null)} className="close-btn">✕</button>
            </div>
            
            <div className="reveal-form">
              <div className="warning">
                <strong>⚠️ WARNING:</strong> This action will log an audit event and temporarily reveal sensitive data.
              </div>
              
              <div className="form-group">
                <label>Field to Reveal:</label>
                <input 
                  type="text" 
                  value={revealModal.field}
                  onChange={(e) => setRevealModal(prev => ({ ...prev, field: e.target.value }))}
                  placeholder="Field name"
                />
              </div>
              
              <div className="form-group">
                <label>Justification (Required):</label>
                <textarea 
                  value={revealModal.reason}
                  onChange={(e) => setRevealModal(prev => ({ ...prev, reason: e.target.value }))}
                  placeholder="Provide legal justification for accessing this sensitive data..."
                  rows={3}
                  required
                />
              </div>
              
              <div className="form-actions">
                <button 
                  onClick={() => setRevealModal(null)}
                  className="cancel-btn"
                >
                  Cancel
                </button>
                <button 
                  onClick={() => handleRevealField(revealModal.field, revealModal.reason)}
                  className="reveal-confirm-btn"
                  disabled={!revealModal.field || !revealModal.reason}
                >
                  🔓 Reveal & Log Audit
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Rules Management Component
const RulesManagement = ({ client }) => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateRule, setShowCreateRule] = useState(false);
  const [newRule, setNewRule] = useState({
    id: '',
    name: '',
    pattern: '',
    action: 'flag',
    severity: 'medium',
    system_scope: [],
    enabled: true
  });
  const [testContent, setTestContent] = useState('');
  const [testResults, setTestResults] = useState(null);
  
  const fetchRules = useCallback(async () => {
    try {
      setLoading(true);
      const response = await client.getRules();
      if (response.code === 'ok') {
        setRules(response.data.rules);
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [client]);
  
  useEffect(() => {
    fetchRules();
  }, [fetchRules]);
  
  const handleTestRule = async () => {
    try {
      const response = await client.dryrunRule(newRule, testContent);
      setTestResults(response.data);
    } catch (err) {
      setTestResults({ error: err.message });
    }
  };
  
  const handlePublishRule = async () => {
    try {
      const response = await client.publishRule(newRule);
      if (response.code === 'ok') {
        alert('Rule published successfully!');
        setShowCreateRule(false);
        setNewRule({
          id: '',
          name: '',
          pattern: '',
          action: 'flag',
          severity: 'medium',
          system_scope: [],
          enabled: true
        });
        fetchRules();
      } else {
        alert(`Error: ${response.message}`);
      }
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };
  
  const systemOptions = ['ldap', 'entrust_idg', 'ums', 'db2', 'service_now', 'llm'];
  
  return (
    <div className="rules-management">
      <div className="rules-header">
        <h3>📜 Policy Rules Management</h3>
        <button 
          onClick={() => setShowCreateRule(true)}
          className="create-rule-btn"
        >
          ➕ Create New Rule
        </button>
      </div>
      
      {loading && <div className="loading">Loading rules...</div>}
      {error && <div className="error">Error: {error}</div>}
      
      {!loading && !error && (
        <div className="rules-table">
          <table>
            <thead>
              <tr>
                <th>Rule ID</th>
                <th>Name</th>
                <th>Action</th>
                <th>Severity</th>
                <th>Systems</th>
                <th>Pattern</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr key={rule.id} className={rule.enabled ? 'enabled' : 'disabled'}>
                  <td className="rule-id">{rule.id}</td>
                  <td>{rule.name}</td>
                  <td>
                    <span className={`action-badge ${rule.action}`}>
                      {rule.action.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <span className={`severity-badge ${rule.severity}`}>
                      {rule.severity.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <div className="systems-list">
                      {rule.system_scope.map(system => (
                        <span key={system} className="system-tag">{system}</span>
                      ))}
                    </div>
                  </td>
                  <td className="pattern-cell">
                    <code>{rule.pattern || 'N/A'}</code>
                  </td>
                  <td>
                    <span className={`status-badge ${rule.enabled ? 'enabled' : 'disabled'}`}>
                      {rule.enabled ? 'ENABLED' : 'DISABLED'}
                    </span>
                  </td>
                  <td>{new Date(rule.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Create Rule Modal */}
      {showCreateRule && (
        <div className="modal-overlay" onClick={() => setShowCreateRule(false)}>
          <div className="modal-content create-rule-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h4>📜 Create New Policy Rule</h4>
              <button onClick={() => setShowCreateRule(false)} className="close-btn">✕</button>
            </div>
            
            <div className="rule-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Rule ID:</label>
                  <input 
                    type="text"
                    value={newRule.id}
                    onChange={(e) => setNewRule(prev => ({ ...prev, id: e.target.value }))}
                    placeholder="e.g., CUSTOM-PII-1"
                  />
                </div>
                
                <div className="form-group">
                  <label>Rule Name:</label>
                  <input 
                    type="text"
                    value={newRule.name}
                    onChange={(e) => setNewRule(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Descriptive rule name"
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>Regex Pattern:</label>
                <input 
                  type="text"
                  value={newRule.pattern}
                  onChange={(e) => setNewRule(prev => ({ ...prev, pattern: e.target.value }))}
                  placeholder="Regular expression pattern"
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Action:</label>
                  <select 
                    value={newRule.action}
                    onChange={(e) => setNewRule(prev => ({ ...prev, action: e.target.value }))}
                  >
                    <option value="allow">Allow</option>
                    <option value="flag">Flag</option>
                    <option value="block">Block</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Severity:</label>
                  <select 
                    value={newRule.severity}
                    onChange={(e) => setNewRule(prev => ({ ...prev, severity: e.target.value }))}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>
              
              <div className="form-group">
                <label>Target Systems:</label>
                <div className="systems-checkboxes">
                  {systemOptions.map(system => (
                    <label key={system} className="checkbox-label">
                      <input 
                        type="checkbox"
                        checked={newRule.system_scope.includes(system)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewRule(prev => ({
                              ...prev,
                              system_scope: [...prev.system_scope, system]
                            }));
                          } else {
                            setNewRule(prev => ({
                              ...prev,
                              system_scope: prev.system_scope.filter(s => s !== system)
                            }));
                          }
                        }}
                      />
                      {system.replace('_', ' ').toUpperCase()}
                    </label>
                  ))}
                </div>
              </div>
              
              <div className="test-section">
                <h5>🧪 Test Rule</h5>
                <div className="form-group">
                  <label>Test Content:</label>
                  <textarea 
                    value={testContent}
                    onChange={(e) => setTestContent(e.target.value)}
                    placeholder="Enter test content to validate rule..."
                    rows={3}
                  />
                </div>
                
                <button onClick={handleTestRule} className="test-btn">
                  🧪 Test Rule
                </button>
                
                {testResults && (
                  <div className="test-results">
                    {testResults.error ? (
                      <div className="error">Test Error: {testResults.error}</div>
                    ) : (
                      <div className={`result ${testResults.matched ? 'matched' : 'no-match'}`}>
                        <strong>Test Result:</strong> {testResults.matched ? '✅ MATCHED' : '❌ NO MATCH'}
                        <br />
                        <strong>Decision:</strong> {testResults.decision}
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              <div className="form-actions">
                <button 
                  onClick={() => setShowCreateRule(false)}
                  className="cancel-btn"
                >
                  Cancel
                </button>
                <button 
                  onClick={handlePublishRule}
                  className="publish-btn"
                  disabled={!newRule.id || !newRule.name || !newRule.pattern || newRule.system_scope.length === 0}
                >
                  📜 Publish Rule
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// 🏛️ **MAIN DASHBOARD COMPONENT**

const JiminiGovernmentDashboard = () => {
  const [client] = useState(() => new JiminiGatewayClient());
  const [activeTab, setActiveTab] = useState('coverage');
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  
  // Test connection on mount
  useEffect(() => {
    const testConnection = async () => {
      try {
        await client.getCoverage();
        setConnectionStatus('connected');
      } catch (error) {
        setConnectionStatus('error');
        console.error('Failed to connect to Jimini Gateway:', error);
      }
    };
    
    testConnection();
  }, [client]);
  
  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected': return '🟢';
      case 'connecting': return '🟡';
      case 'error': return '🔴';
      default: return '⚪';
    }
  };
  
  return (
    <div className="jimini-dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>🛡️ Jimini Policy Gateway</h1>
          <p>PKI Systems Security & Governance Dashboard</p>
        </div>
        
        <div className="header-right">
          <div className="connection-status">
            {getStatusIcon()} {connectionStatus.toUpperCase()}
          </div>
          <div className="tenant-info">
            <strong>Tenant:</strong> {client.tenantId}
          </div>
        </div>
      </header>
      
      <nav className="dashboard-nav">
        <button 
          className={activeTab === 'coverage' ? 'active' : ''}
          onClick={() => setActiveTab('coverage')}
        >
          📊 Coverage
        </button>
        <button 
          className={activeTab === 'decisions' ? 'active' : ''}
          onClick={() => setActiveTab('decisions')}
        >
          📋 Decisions
        </button>
        <button 
          className={activeTab === 'rules' ? 'active' : ''}
          onClick={() => setActiveTab('rules')}
        >
          📜 Rules
        </button>
      </nav>
      
      <main className="dashboard-content">
        {connectionStatus === 'error' && (
          <div className="connection-error">
            <h3>🔴 Connection Error</h3>
            <p>Unable to connect to Jimini Gateway. Please ensure the service is running on port 8000.</p>
            <p>Run: <code>python jimini_gateway.py</code></p>
          </div>
        )}
        
        {connectionStatus === 'connected' && (
          <>
            {activeTab === 'coverage' && <CoverageMetrics client={client} />}
            {activeTab === 'decisions' && <DecisionsLog client={client} />}
            {activeTab === 'rules' && <RulesManagement client={client} />}
          </>
        )}
      </main>
      
      <footer className="dashboard-footer">
        <div className="footer-info">
          <span>🏛️ Government PKI Gateway</span>
          <span>Session: {client.sessionId}</span>
          <span>Last Updated: {new Date().toLocaleTimeString()}</span>
        </div>
      </footer>
    </div>
  );
};

export default JiminiGovernmentDashboard;

// CSS Styles (add to your stylesheet)
const styles = `
.jimini-dashboard {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.header-left h1 {
  margin: 0;
  color: #2c3e50;
  font-size: 24px;
}

.header-left p {
  margin: 5px 0 0 0;
  color: #666;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
}

.connection-status {
  font-weight: bold;
  padding: 4px 8px;
  border-radius: 4px;
  background: #e9ecef;
}

.dashboard-nav {
  display: flex;
  background: white;
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.dashboard-nav button {
  padding: 12px 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 4px;
  margin-right: 8px;
  font-weight: 500;
  transition: all 0.2s;
}

.dashboard-nav button:hover {
  background: #f8f9fa;
}

.dashboard-nav button.active {
  background: #007bff;
  color: white;
}

.dashboard-content {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  min-height: 600px;
}

.loading, .error, .no-data {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error {
  color: #dc3545;
  background: #f8d7da;
  border-radius: 4px;
}

/* Coverage Metrics Styles */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin: 20px 0;
}

.metric-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  border-left: 4px solid #007bff;
}

.metric-card.blocked {
  border-left-color: #dc3545;
}

.metric-card.flagged {
  border-left-color: #ffc107;
}

.metric-card.allowed {
  border-left-color: #28a745;
}

.metric-value {
  font-size: 2em;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 8px;
}

.metric-label {
  color: #666;
  font-size: 0.9em;
}

.systems-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.system-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 12px;
  border: 1px solid #dee2e6;
}

.system-name {
  font-weight: bold;
  margin-bottom: 8px;
  color: #2c3e50;
}

.system-stats {
  display: flex;
  gap: 12px;
}

.system-stats .stat {
  font-size: 0.9em;
}

/* Decisions Log Styles */
.decisions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filters {
  display: flex;
  gap: 10px;
}

.filters select {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.refresh-btn {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.decisions-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9em;
}

.decisions-table th,
.decisions-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.decisions-table th {
  background: #f8f9fa;
  font-weight: 600;
}

.decision-row.block {
  background-color: rgba(220, 53, 69, 0.05);
}

.decision-row.flag {
  background-color: rgba(255, 193, 7, 0.05);
}

.decision-row.allow {
  background-color: rgba(40, 167, 69, 0.05);
}

.rule-badges, .masked-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.rule-badge, .masked-field {
  background: #e9ecef;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.8em;
}

.decision-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 0.8em;
}

.decision-badge.block {
  background: #dc3545;
  color: white;
}

.decision-badge.flag {
  background: #ffc107;
  color: #212529;
}

.decision-badge.allow {
  background: #28a745;
  color: white;
}

.view-btn, .reveal-btn {
  padding: 4px 8px;
  margin-right: 4px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.8em;
}

.view-btn {
  background: #17a2b8;
  color: white;
}

.reveal-btn {
  background: #ffc107;
  color: #212529;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #dee2e6;
}

.modal-header h4 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 5px;
}

.decision-details {
  padding: 20px;
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-section:last-child {
  border-bottom: none;
}

.detail-section h5 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #2c3e50;
}

.rules-list, .citations-list, .masked-fields-list {
  margin-top: 10px;
}

.rule-tag, .system-tag {
  background: #007bff;
  color: white;
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 0.8em;
  margin-right: 5px;
  margin-bottom: 5px;
  display: inline-block;
}

.citation {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.masked-field-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 5px;
}

.field-reveal-btn {
  background: #ffc107;
  color: #212529;
  border: none;
  padding: 4px 8px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.8em;
}

/* Rules Management Styles */
.rules-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.create-rule-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.rules-table table {
  width: 100%;
  border-collapse: collapse;
}

.action-badge, .severity-badge, .status-badge {
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 0.8em;
  font-weight: bold;
}

.action-badge.block {
  background: #dc3545;
  color: white;
}

.action-badge.flag {
  background: #ffc107;
  color: #212529;
}

.action-badge.allow {
  background: #28a745;
  color: white;
}

.severity-badge.critical {
  background: #dc3545;
  color: white;
}

.severity-badge.high {
  background: #fd7e14;
  color: white;
}

.severity-badge.medium {
  background: #ffc107;
  color: #212529;
}

.severity-badge.low {
  background: #6c757d;
  color: white;
}

.status-badge.enabled {
  background: #28a745;
  color: white;
}

.status-badge.disabled {
  background: #6c757d;
  color: white;
}

.pattern-cell code {
  background: #f8f9fa;
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 0.8em;
}

/* Form Styles */
.rule-form {
  padding: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  color: #2c3e50;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 14px;
}

.systems-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.test-section {
  border-top: 1px solid #dee2e6;
  padding-top: 16px;
  margin-top: 16px;
}

.test-btn {
  background: #17a2b8;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 8px;
}

.test-results {
  margin-top: 12px;
  padding: 12px;
  border-radius: 4px;
}

.test-results .result.matched {
  background: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
}

.test-results .result.no-match {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #dee2e6;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.publish-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.publish-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

/* Reveal Form Styles */
.reveal-form {
  padding: 20px;
}

.warning {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  color: #856404;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
}

.reveal-confirm-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.reveal-confirm-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

/* Footer Styles */
.dashboard-footer {
  margin-top: 20px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.footer-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #666;
  font-size: 0.9em;
}

/* Connection Error Styles */
.connection-error {
  text-align: center;
  padding: 40px;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  color: #721c24;
}

.connection-error code {
  background: #fff;
  padding: 4px 8px;
  border-radius: 3px;
  font-family: monospace;
}

/* Responsive Design */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .header-right {
    align-items: center;
  }
  
  .dashboard-nav {
    flex-direction: column;
  }
  
  .dashboard-nav button {
    margin-bottom: 4px;
    margin-right: 0;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .footer-info {
    flex-direction: column;
    gap: 8px;
  }
  
  .modal-content {
    margin: 20px;
    max-width: calc(100% - 40px);
  }
}
`;

// Export styles for use
export { styles };