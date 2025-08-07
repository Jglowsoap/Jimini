from datetime import datetime
from app.models import AuditRecord
from app.audit import append_audit

def evaluate(text: str, agent_id: str, rules_store: dict):
    matched = []
    for rid, (rule, regex) in rules_store.items():
        if regex.search(text):
            matched.append((rule, rid))

    if any(rule.action == 'block' for rule, _ in matched):
        decision = 'block'
    elif any(rule.action == 'flag' for rule, _ in matched):
        decision = 'flag'
    else:
        decision = 'allow'

    rule_ids = [rid for _, rid in matched]

    record = AuditRecord(
        timestamp=datetime.utcnow().isoformat() + 'Z',
        agent_id=agent_id,
        decision=decision,
        rule_ids=rule_ids,
        excerpt=text[:200]
    )
    append_audit(record)
    return decision, rule_ids
