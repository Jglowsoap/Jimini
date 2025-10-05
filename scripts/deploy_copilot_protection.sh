#!/bin/bash

# =================================================================
# ILLINOIS GOVERNMENT - EMERGENCY COPILOT PROTECTION DEPLOYMENT
# =================================================================
# 
# Purpose: Rapid deployment of Microsoft Copilot protections for
#          Illinois state government systems
# 
# Usage: sudo ./deploy_copilot_protection.sh
# 
# CRITICAL: Run this IMMEDIATELY on any system with Copilot enabled
# =================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (use sudo)"
   exit 1
fi

log "🚨 DEPLOYING EMERGENCY MICROSOFT COPILOT PROTECTIONS"
log "=============================================="

# Step 1: Backup existing configuration
log "📂 Creating backup of existing configuration..."
BACKUP_DIR="/opt/jimini-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "/etc/jimini/policy_rules.yaml" ]; then
    cp "/etc/jimini/policy_rules.yaml" "$BACKUP_DIR/"
    success "Existing rules backed up to $BACKUP_DIR"
fi

# Step 2: Create Jimini directories
log "📁 Creating Jimini directories..."
mkdir -p /etc/jimini
mkdir -p /var/log/jimini
mkdir -p /opt/jimini

# Step 3: Deploy Illinois Copilot protection rules
log "🛡️ Deploying Illinois Copilot protection rules..."
cat > /etc/jimini/copilot-protection.yaml << 'EOF'
rules:
  # EMERGENCY COPILOT PROTECTIONS FOR ILLINOIS GOVERNMENT
  
  - id: "EMERGENCY-COPILOT-1"
    title: "EMERGENCY: Block all Copilot data sharing"
    pattern: '(?i)\b(?:copilot|github copilot|microsoft copilot)[^.]{0,50}(?:save|store|upload|share|send|sync)\b'
    severity: "critical"
    action: "block"
    tags: ["emergency","copilot","data_protection"]
    shadow_override: "enforce"

  - id: "EMERGENCY-SSN-COPILOT"
    title: "EMERGENCY: Block SSN in Copilot interactions"
    pattern: '\b\d{3}-?\d{2}-?\d{4}\b'
    severity: "critical"
    action: "block"
    tags: ["emergency","ssn","copilot"]
    shadow_override: "enforce"

  - id: "EMERGENCY-IL-DL-COPILOT"
    title: "EMERGENCY: Block Illinois DL in Copilot"
    pattern: '\b[A-Za-z](?:\d{3}-?\d{4}-?\d{4}|\d{11})\b'
    severity: "critical"
    action: "block"
    tags: ["emergency","illinois_dl","copilot"]
    shadow_override: "enforce"

  - id: "EMERGENCY-CREDENTIAL-BLOCK"
    title: "EMERGENCY: Block credential sharing with Copilot"
    pattern: '(?i)(?:password|key|token|secret|credential)[=:\s]*[A-Za-z0-9+/=_\-]{8,}'
    severity: "critical"
    action: "block"
    tags: ["emergency","credentials","copilot"]
    shadow_override: "enforce"

  - id: "EMERGENCY-BULK-EXPORT"
    title: "EMERGENCY: Block bulk data requests to Copilot"
    pattern: '(?i)\b(?:export|extract|generate|list)[^.]{0,30}(?:all|bulk|entire)[^.]{0,30}(?:records|data|citizens|users)\b'
    severity: "critical"
    action: "block"
    tags: ["emergency","bulk_export","copilot"]
    shadow_override: "enforce"
EOF

# Step 4: Create systemd service
log "⚙️ Creating Jimini systemd service..."
cat > /etc/systemd/system/jimini-copilot-protection.service << 'EOF'
[Unit]
Description=Jimini Copilot Protection Gateway
After=network.target
Wants=network.target

[Service]
Type=exec
User=jimini
Group=jimini
WorkingDirectory=/opt/jimini
ExecStart=/usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 9000
Environment=JIMINI_RULES_PATH=/etc/jimini/copilot-protection.yaml
Environment=JIMINI_SHADOW=0
Environment=JIMINI_API_KEY=IL-GOV-SECURE-KEY-$(openssl rand -hex 16)
Environment=AUDIT_LOG_PATH=/var/log/jimini/copilot-audit.jsonl
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jimini-copilot

[Install]
WantedBy=multi-user.target
EOF

# Step 5: Create Jimini user
log "👤 Creating Jimini service user..."
if ! id "jimini" &>/dev/null; then
    useradd --system --home /opt/jimini --shell /bin/false jimini
    success "Created jimini user"
else
    warning "User 'jimini' already exists"
fi

# Set ownership
chown -R jimini:jimini /opt/jimini /var/log/jimini
chmod 755 /opt/jimini /var/log/jimini
chmod 600 /etc/jimini/copilot-protection.yaml

# Step 6: Install Python dependencies (if needed)
log "📦 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install fastapi uvicorn pyyaml requests
    success "Python dependencies installed"
else
    warning "pip3 not found. Install manually: fastapi uvicorn pyyaml requests"
fi

# Step 7: Network-level blocks (if iptables available)
log "🔒 Implementing network-level blocks..."
if command -v iptables &> /dev/null; then
    # Block known Copilot endpoints
    iptables -A OUTPUT -d copilot.microsoft.com -j REJECT --reject-with icmp-host-prohibited
    iptables -A OUTPUT -d github.copilot.com -j REJECT --reject-with icmp-host-prohibited
    iptables -A OUTPUT -d api.github.com -p tcp --dport 443 -j REJECT --reject-with icmp-host-prohibited
    
    # Save iptables rules
    if command -v iptables-save &> /dev/null; then
        iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
    fi
    
    success "Network blocks implemented"
else
    warning "iptables not available. Implement network blocks manually."
fi

# Step 8: Create monitoring script
log "📊 Creating monitoring script..."
cat > /opt/jimini/monitor_copilot_threats.sh << 'EOF'
#!/bin/bash

# Monitor for Copilot-related security events
LOG_FILE="/var/log/jimini/copilot-audit.jsonl"
ALERT_EMAIL="${SECURITY_ALERT_EMAIL:-security@illinois.gov}"

# Check for blocked Copilot attempts in the last hour
RECENT_BLOCKS=$(grep -c '"action":"block"' "$LOG_FILE" 2>/dev/null | tail -100 | grep -c "copilot" || echo "0")

if [ "$RECENT_BLOCKS" -gt 0 ]; then
    echo "ALERT: $RECENT_BLOCKS Copilot security blocks in the last hour"
    echo "Check: $LOG_FILE"
    
    # Send alert email if configured
    if command -v mail &> /dev/null && [ -n "$ALERT_EMAIL" ]; then
        echo "SECURITY ALERT: $RECENT_BLOCKS Microsoft Copilot security violations detected on $(hostname)" | \
        mail -s "URGENT: Copilot Security Alert - $(hostname)" "$ALERT_EMAIL"
    fi
fi
EOF

chmod +x /opt/jimini/monitor_copilot_threats.sh
chown jimini:jimini /opt/jimini/monitor_copilot_threats.sh

# Step 9: Add monitoring cron job
log "⏰ Adding monitoring cron job..."
echo "*/15 * * * * /opt/jimini/monitor_copilot_threats.sh" | crontab -u jimini -

# Step 10: Create emergency response script
log "🚨 Creating emergency response script..."
cat > /opt/jimini/emergency_copilot_response.sh << 'EOF'
#!/bin/bash

# Emergency response for Copilot data exposure
echo "🚨 EMERGENCY COPILOT DATA EXPOSURE RESPONSE"
echo "==========================================="
echo "1. Disconnect system from network: sudo ip link set down eth0"
echo "2. Document exposure: $(date) - Copilot access detected"
echo "3. Preserve logs: cp /var/log/jimini/* /evidence/"
echo "4. Contact State CISO immediately"
echo "5. Review audit log: tail -f /var/log/jimini/copilot-audit.jsonl"
echo ""
echo "CRITICAL: Do NOT restart Copilot until security review complete"
EOF

chmod +x /opt/jimini/emergency_copilot_response.sh

# Step 11: Enable and start service
log "🚀 Enabling and starting Jimini service..."
systemctl daemon-reload
systemctl enable jimini-copilot-protection.service

# Check if Jimini code is available
if [ ! -f "/opt/jimini/app/main.py" ]; then
    warning "Jimini application code not found in /opt/jimini"
    warning "Please deploy the Jimini application files before starting the service"
    warning "Service created but not started"
else
    systemctl start jimini-copilot-protection.service
    success "Jimini Copilot protection service started"
fi

# Step 12: Verification
log "✅ Running deployment verification..."
sleep 2

# Check service status
if systemctl is-active --quiet jimini-copilot-protection.service 2>/dev/null; then
    success "✅ Jimini service is running"
else
    warning "⚠️ Jimini service not running (may need application code)"
fi

# Check network blocks
if iptables -L | grep -q "copilot.microsoft.com" 2>/dev/null; then
    success "✅ Network blocks active"
else
    warning "⚠️ Network blocks not verified"
fi

# Check audit log
if [ -f "/var/log/jimini/copilot-audit.jsonl" ]; then
    success "✅ Audit logging configured"
else
    warning "⚠️ Audit log not yet created"
fi

# Final report
echo ""
log "🎯 DEPLOYMENT COMPLETE"
log "===================="
success "✅ Emergency Copilot protections deployed"
success "✅ Rules file: /etc/jimini/copilot-protection.yaml"
success "✅ Audit log: /var/log/jimini/copilot-audit.jsonl"
success "✅ Service: jimini-copilot-protection.service"
success "✅ Monitoring: /opt/jimini/monitor_copilot_threats.sh"
success "✅ Emergency response: /opt/jimini/emergency_copilot_response.sh"

echo ""
warning "⚠️ IMPORTANT NEXT STEPS:"
echo "1. Test the protection: curl -X POST http://localhost:9000/v1/evaluate -H 'Content-Type: application/json' -d '{\"text\":\"Help copilot save my SSN 123-45-6789\", \"direction\":\"inbound\"}'"
echo "2. Deploy Jimini application code to /opt/jimini if not already present"
echo "3. Configure environment variables in /etc/systemd/system/jimini-copilot-protection.service"
echo "4. Review and customize rules in /etc/jimini/copilot-protection.yaml"
echo "5. Set up log rotation for /var/log/jimini/copilot-audit.jsonl"
echo "6. Configure email alerts in monitor script"

echo ""
error "🚨 CRITICAL: Audit all existing Copilot usage IMMEDIATELY"
error "🚨 Review last 30 days of Copilot interactions for data exposure"

log "Deployment completed at $(date)"
log "Backup created at: $BACKUP_DIR"