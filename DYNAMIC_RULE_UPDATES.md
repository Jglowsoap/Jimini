# Jimini API: Dynamic Rule Updates

## Overview

The Jimini API now supports updating existing rules on the fly, including changing a rule's action from `block` to `flag` (or any other action). This capability allows dynamic policy adjustments without restarting the service.

## API Endpoints

### Update Rule Action

**Endpoint:** `PUT /v1/rules/{rule_id}`

**Description:** Update any property of an existing policy rule, including its action.

**Authentication:** Uses the same API key as other endpoints (`X-API-Key` header).

**Request Body:**
```json
{
  "action": "flag"  // or "block", "allow"
}
```

**Complete Request Body Options:**
```json
{
  "title": "Updated rule title",
  "severity": "warning",  // "error", "warning", "info"
  "pattern": "new regex pattern",
  "min_count": 2,
  "max_chars": 1000,
  "llm_prompt": "Custom LLM validation prompt",
  "applies_to": ["user_input", "prompt"],
  "endpoints": ["/*", "/api/*"],
  "action": "flag",  // "block", "flag", "allow"
  "shadow_override": "enforce"  // optional
}
```

### Get Current Rule

**Endpoint:** `GET /v1/rules/{rule_id}`

**Description:** Retrieve the current configuration of a specific rule.

**Response:**
```json
{
  "id": "GITHUB-TOKEN-1.0",
  "title": "Secret: GitHub Personal Access Token",
  "severity": "error",
  "pattern": "\\bghp_[A-Za-z0-9]{36}\\b",
  "min_count": 1,
  "max_chars": null,
  "llm_prompt": null,
  "applies_to": ["user_input", "prompt"],
  "endpoints": ["/*"],
  "action": "block",
  "shadow_override": "enforce"
}
```

## Examples

### 1. Change Rule from BLOCK to FLAG

```bash
# Get current rule status
curl -X GET "http://localhost:9000/v1/rules/GITHUB-TOKEN-1.0" \
  -H "X-API-Key: changeme"

# Update rule action to flag
curl -X PUT "http://localhost:9000/v1/rules/GITHUB-TOKEN-1.0" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme" \
  -d '{"action": "flag"}'
```

### 2. Using Python

```python
import requests

# Configuration
base_url = "http://localhost:9000"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "changeme"
}

# Get current rule
response = requests.get(f"{base_url}/v1/rules/GITHUB-TOKEN-1.0", headers=headers)
current_rule = response.json()
print(f"Current action: {current_rule['action']}")

# Update rule action
update_data = {"action": "flag"}
response = requests.put(
    f"{base_url}/v1/rules/GITHUB-TOKEN-1.0", 
    headers=headers,
    json=update_data
)

if response.status_code == 200:
    updated_rule = response.json()
    print(f"Updated action: {updated_rule['action']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### 3. Using the Demo Script

```bash
# Change to flag
python demo_rule_update.py --rule-id GITHUB-TOKEN-1.0 --new-action flag

# Change back to block
python demo_rule_update.py --rule-id GITHUB-TOKEN-1.0 --new-action block

# With testing
python demo_rule_update.py --rule-id GITHUB-TOKEN-1.0 --new-action flag --test
```

## Key Features

### 1. **Real-time Updates**
- Changes are applied immediately to the in-memory rule store
- No service restart required
- New evaluations use the updated rules instantly

### 2. **Persistent Storage**
- Rule changes are automatically written back to the YAML file
- Changes persist across service restarts
- Backup files are created for safety

### 3. **Hot Reloading**
- The rules_loader watches for file changes
- Manual file edits are also picked up automatically
- Memory and file stay synchronized

### 4. **Validation**
- All rule updates are validated before applying
- Regex patterns are compiled and tested
- Invalid configurations are rejected

### 5. **Atomic Operations**
- Updates are applied atomically
- Failed updates don't corrupt existing rules
- Rollback capability with backup files

## Rule Actions

| Action | Description | Behavior |
|--------|-------------|----------|
| `block` | Block the request | Returns `decision: "block"`, stops processing |
| `flag` | Flag but allow | Returns `decision: "flag"`, continues processing |
| `allow` | Explicitly allow | Returns `decision: "allow"`, lower priority than block/flag |

## Error Handling

### Common Error Codes

- **400 Bad Request:** Invalid rule data or validation failed
- **403 Forbidden:** Admin access required (if RBAC enabled)
- **404 Not Found:** Rule ID doesn't exist
- **422 Unprocessable Entity:** Request format errors

### Example Error Response
```json
{
  "detail": "Rule validation failed: Invalid regex pattern"
}
```

## Security Considerations

### Authentication
- Uses standard Jimini API key authentication
- Same `X-API-Key` header as other endpoints
- Default key: `changeme` (change in production)

### Authorization
- RBAC can be enabled for admin-only access
- Currently disabled by default (`rbac_enabled: false`)
- When enabled, requires `ADMIN` role for rule modifications

### Audit Trail
- All rule changes are logged in the audit system
- Includes who made the change and when
- Tamper-evident audit chain for compliance

## Best Practices

1. **Test Changes First:** Use the validation endpoint before applying updates
2. **Backup Rules:** Keep backups of your rule files before major changes
3. **Monitor Impact:** Check rule statistics after changes
4. **Use Shadow Mode:** Test rule changes in shadow mode first
5. **Gradual Rollout:** Change rules incrementally rather than all at once

## Implementation Details

The dynamic rule update functionality is implemented through:

- **Rule Manager (`app/rule_management.py`):** Handles CRUD operations
- **Rules Store (`app/rules_loader.py`):** In-memory rule storage with hot reloading
- **Persistence Layer:** YAML file read/write with atomic operations
- **Validation Engine:** Regex compilation and rule syntax checking
- **API Layer (`app/main.py`):** RESTful endpoints with proper error handling

Changes are immediately reflected in policy evaluations, making this suitable for real-time policy adjustments in production environments.