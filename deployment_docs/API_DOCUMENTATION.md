# Jimini API Documentation

## Authentication
All API requests require the `api_key` parameter matching `JIMINI_API_KEY` environment variable.

## Endpoints

### POST /v1/evaluate
Evaluate text content against security rules.

**Request Body:**
```json
{
  "text": "string (required) - Text content to evaluate",
  "api_key": "string (required) - API authentication key",
  "context": "string (optional) - Additional context for evaluation",
  "endpoint": "string (optional) - Endpoint identifier for rule filtering"
}
```

**Response:**
```json
{
  "decision": "allow|flag|block",
  "rule_ids": ["array of matched rule IDs"],
  "risk_score": "number (0-100)",
  "processing_time_ms": "number",
  "audit_id": "string"
}
```

### GET /v1/metrics
Retrieve security metrics and statistics.

### GET /v1/audit/verify
Verify audit log integrity using SHA3-256 chain.

### GET /v1/audit/sarif
Export audit logs in SARIF format.

### GET /health
Health check endpoint for monitoring.
